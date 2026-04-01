import os
import requests
import re
import secrets
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
import random
import string
from flask_socketio import SocketIO, join_room, leave_room, emit

# 配置常量
TEMP_DIR = './temp'
ASSETS_DIR = './assets'
INSTANCE_DIR = './instance'
STICKERS_DIR = './stickers'  # 表情包缓存目录
MAX_MESSAGE_HISTORY = 20
STICKER_API_BASE = 'http://45.207.204.145:5003/api'  # 表情包服务器地址

# 创建必要的目录
for directory in [TEMP_DIR, INSTANCE_DIR, STICKERS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# 应用初始化
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(32)  # 生成安全的密钥
# 使用绝对路径确保数据库文件路径正确
db_path = os.path.join(os.path.abspath(INSTANCE_DIR), 'users.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 设置session永久不过期
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365 * 10)  # 10年有效期

# 数据库和登录管理器初始化
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# SocketIO 初始化
socketio = SocketIO(app, async_mode='threading')

# 全局存储
room_users = {}  # 用于存储聊天室中的用户
message_history = {}  # 用于存储消息历史
user_sessions = {}  # 用于存储用户会话信息

# 数据库模型
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_super_admin = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    passkey_used = db.Column(db.String(6), nullable=True)  # 用户注册时使用的 Passkey
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Passkey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(6), unique=True, nullable=False)
    duration_days = db.Column(db.Integer, nullable=True)  # None 表示无限时长
    max_uses = db.Column(db.Integer, nullable=True)  # None 表示无限使用次数
    current_uses = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    def is_valid(self):
        """检查 Passkey 是否有效"""
        # 检查是否激活
        if not self.is_active:
            return False
        
        # 检查是否过期
        if self.expires_at:
            # 使用相同的时区进行比较
            if datetime.now(timezone.utc) > self.expires_at.astimezone(timezone.utc):
                return False
        
        # 检查使用次数
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        
        return True

class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=True)  # 可选密码
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)

# 用户表情包模型
class UserSticker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sticker_code = db.Column(db.String(20), nullable=False)  # 表情码
    sticker_type = db.Column(db.String(20), nullable=False)  # 'single' 或 'pack'
    sticker_name = db.Column(db.String(100), nullable=True)  # 表情名称
    description = db.Column(db.String(255), nullable=True)  # 描述
    local_path = db.Column(db.String(255), nullable=False)  # 本地缓存路径
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 联合唯一约束：一个用户不能重复添加同一个表情
    __table_args__ = (db.UniqueConstraint('user_id', 'sticker_code', name='unique_user_sticker'),)

# 表情包合集中的表情模型（用于存储合集内的表情）
class PackSticker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pack_code = db.Column(db.String(20), nullable=False)  # 所属表情包合集码
    sticker_code = db.Column(db.String(50), nullable=False)  # 表情码（可能是生成的）
    sticker_name = db.Column(db.String(100), nullable=True)  # 表情名称
    description = db.Column(db.String(255), nullable=True)  # 描述
    local_path = db.Column(db.String(255), nullable=False)  # 本地缓存路径
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # 联合唯一约束：一个合集中不能有重复的表情码
    __table_args__ = (db.UniqueConstraint('user_id', 'pack_code', 'sticker_code', name='unique_pack_sticker'),)

# 登录管理
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 工具函数
def get_bing_wallpaper():
    """获取必应今日美图并保存到本地"""
    try:
        bing_api_url = 'https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=zh-CN'
        response = requests.get(bing_api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('images'):
                image_url = 'https://www.bing.com' + data['images'][0]['url']
                image_response = requests.get(image_url, timeout=10)
                if image_response.status_code == 200:
                    wallpaper_path = os.path.join(TEMP_DIR, 'bing_wallpaper.jpg')
                    with open(wallpaper_path, 'wb') as f:
                        f.write(image_response.content)
                    return '/temp/bing_wallpaper.jpg'
    except Exception as e:
        print(f"获取必应壁纸失败: {e}")
    return None

def get_poetry():
    """从服务端获取今日诗词"""
    try:
        response = requests.get('https://v1.jinrishici.com/all.json', timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"获取诗词失败: {e}")
    return {
        "content": "日暮秋烟起，萧萧枫树林。",
        "origin": "过三闾庙",
        "author": "戴叔伦",
        "category": "古诗文-四季-秋天"
    }

def generate_passkey():
    """生成6位随机Passkey（数字+大写字母）"""
    characters = string.ascii_uppercase + string.digits
    while True:
        key = ''.join(random.choice(characters) for _ in range(6))
        # 检查是否已存在
        if not Passkey.query.filter_by(key=key).first():
            return key

def get_utc_plus_8_time():
    """获取UTC+8时间"""
    return datetime.now(timezone(timedelta(hours=8)))

# 路由
@app.route('/')
def index():
    wallpaper_url = get_bing_wallpaper()
    poetry = get_poetry()
    return render_template('index.html', wallpaper_url=wallpaper_url, poetry=poetry)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('board'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # 登录用户并设置session为永久
            login_user(user, remember=True)
            # 标记session为永久
            session.permanent = True
            
            # 实现顶号功能：记录当前用户的session ID
            user_sessions[username] = request.cookies.get('session')
            
            return redirect(url_for('board'))
        else:
            flash('用户名或密码错误')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('board'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        passkey = request.form.get('passkey', '')
        
        # 检查是否是第一个用户
        is_first_user = User.query.count() == 0
        
        # 首个用户不需要 Passkey，其他用户需要验证 Passkey
        if not is_first_user:
            passkey_obj = Passkey.query.filter_by(key=passkey).first()
            if not passkey_obj or not passkey_obj.is_valid():
                flash('无效的Passkey')
                return redirect(url_for('register'))
            
            # 增加使用次数
            passkey_obj.current_uses += 1
            if passkey_obj.max_uses and passkey_obj.current_uses >= passkey_obj.max_uses:
                passkey_obj.is_active = False
            db.session.commit()
        
        if password != confirm_password:
            flash('两次输入的密码不一致')
            return redirect(url_for('register'))
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('register'))
        
        # 创建新用户
        user = User(
            username=username,
            is_super_admin=is_first_user,
            is_admin=is_first_user,  # 首个用户同时是管理员
            passkey_used=passkey if not is_first_user else None  # 保存使用的 Passkey
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功，请登录')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/board')
@login_required
def board():
    return render_template('board.html', 
                         username=current_user.username, 
                         passkey_used=current_user.passkey_used,
                         is_admin=current_user.is_admin, 
                         is_super_admin=current_user.is_super_admin)

@app.route('/board/users')
@login_required
def user_management():
    if not (current_user.is_admin or current_user.is_super_admin):
        flash('权限不足')
        return redirect(url_for('board'))
    
    users = User.query.all()
    return render_template('user_management.html', 
                         users=users,
                         username=current_user.username, 
                         passkey_used=current_user.passkey_used,
                         is_admin=current_user.is_admin, 
                         is_super_admin=current_user.is_super_admin)

@app.route('/board/passkeys')
@login_required
def passkey_management():
    if not current_user.is_super_admin:
        flash('权限不足')
        return redirect(url_for('board'))
    
    # 获取所有Passkey
    passkeys = Passkey.query.all()
    return render_template('passkey_management.html', 
                         passkeys=passkeys,
                         username=current_user.username, 
                         passkey_used=current_user.passkey_used,
                         is_admin=current_user.is_admin, 
                         is_super_admin=current_user.is_super_admin)

@app.route('/api/users', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_users():
    if not (current_user.is_admin or current_user.is_super_admin):
        return jsonify({'error': '权限不足'}), 403
    
    if request.method == 'GET':
        users = User.query.all()
        return jsonify([{
            'id': user.id,
            'username': user.username,
            'is_super_admin': user.is_super_admin,
            'is_admin': user.is_admin,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        } for user in users])
    
    elif request.method == 'POST':
        data = request.json
        if not current_user.is_super_admin and data.get('is_admin'):
            return jsonify({'error': '只有超级管理员可以创建管理员用户'}), 403
        
        user = User(
            username=data['username'],
            is_admin=data.get('is_admin', False),
            is_super_admin=False
        )
        user.set_password(data['password'])
        db.session.add(user)
        db.session.commit()
        return jsonify({'id': user.id, 'username': user.username})
    
    elif request.method == 'PUT':
        data = request.json
        user = User.query.get(data['id'])
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        if user.is_super_admin:
            return jsonify({'error': '超级管理员不可修改'}), 403
        
        if not current_user.is_super_admin and user.is_admin:
            return jsonify({'error': '只有超级管理员可以修改管理员用户'}), 403
        
        if 'password' in data:
            user.set_password(data['password'])
        if 'is_admin' in data and current_user.is_super_admin:
            user.is_admin = data['is_admin']
        db.session.commit()
        return jsonify({'id': user.id, 'username': user.username})
    
    elif request.method == 'DELETE':
        user_id = request.json['id']
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        if user.is_super_admin:
            return jsonify({'error': '超级管理员不可删除'}), 403
        
        if not current_user.is_super_admin and user.is_admin:
            return jsonify({'error': '只有超级管理员可以删除管理员用户'}), 403
        
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True})

@app.route('/api/passkeys', methods=['GET', 'POST', 'DELETE'])
@login_required
def api_passkeys():
    if not current_user.is_super_admin:
        return jsonify({'error': '权限不足'}), 403
    
    if request.method == 'GET':
        passkeys = Passkey.query.all()
        return jsonify([{
            'id': p.id,
            'key': p.key,
            'duration_days': p.duration_days,
            'max_uses': p.max_uses,
            'current_uses': p.current_uses,
            'created_at': p.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'expires_at': p.expires_at.strftime('%Y-%m-%d %H:%M:%S') if p.expires_at else None,
            'is_active': p.is_active,
            'is_valid': p.is_valid()
        } for p in passkeys])
    
    elif request.method == 'POST':
        data = request.json
        duration_days = data.get('duration_days')
        max_uses = data.get('max_uses')
        
        # 生成新的Passkey
        key = generate_passkey()
        
        # 计算过期时间
        expires_at = None
        if duration_days:
            expires_at = get_utc_plus_8_time() + timedelta(days=duration_days)
        
        # 创建Passkey
        passkey = Passkey(
            key=key,
            duration_days=duration_days,
            max_uses=max_uses,
            expires_at=expires_at
        )
        db.session.add(passkey)
        db.session.commit()
        
        return jsonify({
            'id': passkey.id,
            'key': passkey.key,
            'duration_days': passkey.duration_days,
            'max_uses': passkey.max_uses,
            'current_uses': passkey.current_uses,
            'created_at': passkey.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'expires_at': passkey.expires_at.strftime('%Y-%m-%d %H:%M:%S') if passkey.expires_at else None,
            'is_active': passkey.is_active
        })
    
    elif request.method == 'DELETE':
        passkey_id = request.json['id']
        passkey = Passkey.query.get(passkey_id)
        if not passkey:
            return jsonify({'error': 'Passkey不存在'}), 404
        
        db.session.delete(passkey)
        db.session.commit()
        return jsonify({'success': True})

# 静态文件服务
@app.route('/temp/<path:filename>')
def serve_temp(filename):
    return send_from_directory(TEMP_DIR, filename)

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(ASSETS_DIR, filename)

# WebSocket 事件处理
@socketio.on('join_room')
def handle_join_room(data):
    try:
        room = data.get('room')
        username = data.get('username')
        
        if not room or not username:
            return
        
        # 加入房间
        join_room(room)
        
        # 记录用户在房间中
        if room not in room_users:
            room_users[room] = []
        if username not in room_users[room]:
            room_users[room].append(username)
        
        # 广播用户加入消息
        current_time = get_utc_plus_8_time()
        emit('user_joined', {
            'username': username,
            'message': f'{username} 加入了聊天室',
            'timestamp': current_time.strftime('%H:%M:%S')
        }, room=room)
        
        # 更新用户列表
        emit('user_list', {
            'room': room,
            'users': room_users[room]
        }, room=room)
    except Exception as e:
        print(f"处理加入房间事件失败: {e}")

@socketio.on('leave_room')
def handle_leave_room(data):
    try:
        room = data.get('room')
        username = data.get('username')
        
        if not room or not username:
            return
        
        # 离开房间
        leave_room(room)
        
        # 从房间用户列表中移除
        if room in room_users and username in room_users[room]:
            room_users[room].remove(username)
        
        # 广播用户离开消息
        current_time = get_utc_plus_8_time()
        emit('user_left', {
            'username': username,
            'message': f'{username} 离开了聊天室',
            'timestamp': current_time.strftime('%H:%M:%S')
        }, room=room)
        
        # 更新用户列表
        emit('user_list', {
            'room': room,
            'users': room_users.get(room, [])
        }, room=room)
    except Exception as e:
        print(f"处理离开房间事件失败: {e}")

@socketio.on('send_message')
def handle_send_message(data):
    try:
        room = data.get('room')
        username = data.get('username')
        message = data.get('message')
        
        if not room or not username or not message:
            return
        
        # 记录消息历史
        if room not in message_history:
            message_history[room] = []
        
        # 使用UTC+8时间
        current_time = get_utc_plus_8_time()
        message_data = {
            'username': username,
            'message': message,
            'timestamp': current_time.strftime('%H:%M:%S'),
            'is_self': False,
            'quoted_message': data.get('quoted_message'),
            'quoted_messages': data.get('quoted_messages')
        }
        
        message_history[room].append(message_data)
        
        # 只保留最近20条消息
        if len(message_history[room]) > MAX_MESSAGE_HISTORY:
            message_history[room] = message_history[room][-MAX_MESSAGE_HISTORY:]
        
        # 广播消息
        emit('new_message', message_data, room=room)
    except Exception as e:
        print(f"处理发送消息事件失败: {e}")

@socketio.on('get_message_history')
def handle_get_message_history(data):
    try:
        room = data.get('room')
        username = data.get('username')
        
        if not room or not username:
            return
        
        # 获取消息历史
        history = message_history.get(room, [])
        
        # 标记自己的消息
        for msg in history:
            msg['is_self'] = (msg['username'] == username)
        
        emit('message_history', {
            'room': room,
            'messages': history
        })
    except Exception as e:
        print(f"处理获取消息历史事件失败: {e}")
        # 发送空的消息历史，避免前端解析错误
        emit('message_history', {
            'room': data.get('room', ''),
            'messages': []
        })

# 聊天室相关路由
@app.route('/board/chat')
@login_required
def chat():
    # 获取所有活跃的聊天室
    chat_rooms = ChatRoom.query.filter_by(is_active=True).all()
    return render_template('chat.html', 
                         username=current_user.username, 
                         passkey_used=current_user.passkey_used,
                         chat_rooms=chat_rooms, 
                         is_admin=current_user.is_admin, 
                         is_super_admin=current_user.is_super_admin)

@app.route('/board/tools')
@login_required
def tools():
    return render_template('tools.html', 
                         username=current_user.username, 
                         passkey_used=current_user.passkey_used,
                         is_admin=current_user.is_admin, 
                         is_super_admin=current_user.is_super_admin)

# 小说阅读器相关路由和API
NOVELS_DIR = './instance/novels'

# 创建小说目录
if not os.path.exists(NOVELS_DIR):
    os.makedirs(NOVELS_DIR)

def read_file_with_encoding(file_path):
    """读取文件并自动检测编码"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16', 'utf-8-sig']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            continue
    
    # 如果所有编码都失败，尝试使用errors='replace'模式
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return content
    except:
        return ''

@app.route('/tools/novelreader')
@login_required
def novel_reader():
    return render_template('novel_reader.html', 
                         username=current_user.username)

@app.route('/api/novels', methods=['GET'])
@login_required
def get_novels():
    """获取小说列表"""
    try:
        novels = []
        if os.path.exists(NOVELS_DIR):
            for filename in os.listdir(NOVELS_DIR):
                if filename.endswith('.txt'):
                    novel_name = filename[:-4]  # 去掉.txt后缀
                    novels.append({
                        'name': novel_name,
                        'filename': filename
                    })
        return jsonify({
            'success': True,
            'novels': novels
        })
    except Exception as e:
        print(f"获取小说列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def parse_chapters(content):
    """解析小说章节
    
    章节格式：
    - 筛选所有空行，将其下方标记为新的一段
    - 开头到第一个空行也是一段
    - 最后一个空行到结尾也是一段
    - 例外1：如果前10行同时包含"作者："和"简介："，则忽略开头到第一空行，从第一空行下方开始计算为第一章
    - 例外2：如果前20行包含单独一行的"正文"二字，则从它下方第一个有文字的非空行开始计算章节id1
    """
    chapters = []
    lines = content.split('\n')
    
    # 检查前10行是否同时包含"作者："和"简介："
    has_author_intro = False
    if len(lines) >= 10:
        first_10_lines = '\n'.join(lines[:10])
        if '作者：' in first_10_lines and '简介：' in first_10_lines:
            has_author_intro = True
    
    # 检查前20行是否包含单独一行的"正文"二字
    has_body_marker = False
    body_marker_index = -1
    if len(lines) >= 20:
        for i, line in enumerate(lines[:20]):
            if line.strip() == '正文':
                has_body_marker = True
                body_marker_index = i
                break
    
    # 确定开始解析的位置
    start_index = 0
    if has_body_marker:
        # 从"正文"下方第一个非空行开始解析
        start_index = body_marker_index + 1
        # 跳过空行
        while start_index < len(lines) and lines[start_index].strip() == '':
            start_index += 1
    elif has_author_intro:
        # 找到第一个空行的位置
        first_empty_line = -1
        for i, line in enumerate(lines):
            if line.strip() == '':
                first_empty_line = i
                break
        if first_empty_line != -1:
            # 从第一空行下方开始解析
            start_index = first_empty_line + 1
            # 跳过空行
            while start_index < len(lines) and lines[start_index].strip() == '':
                start_index += 1
    
    if start_index >= len(lines):
        # 内容为空
        return []
    
    # 开始解析章节
    current_chapter = None
    current_content = []
    
    # 处理第一个章节
    if start_index < len(lines):
        # 如果是例外情况，第一行作为章节名
        if has_body_marker or has_author_intro:
            current_chapter = lines[start_index].strip()
            start_index += 1
        else:
            current_chapter = '第1章'
    
    # 遍历剩余行
    for i in range(start_index, len(lines)):
        line = lines[i]
        line_stripped = line.strip()
        
        # 检查是否是空行
        if line_stripped == '':
            # 保存当前章节
            if current_chapter is not None and current_content:
                chapters.append({
                    'name': current_chapter,
                    'content': '\n'.join(current_content).strip()
                })
                current_content = []
            
            # 找到下一个非空行作为章节名
            next_index = i + 1
            while next_index < len(lines) and lines[next_index].strip() == '':
                next_index += 1
            
            if next_index < len(lines):
                # 新章节名
                current_chapter = lines[next_index].strip()
                i = next_index  # 跳过下一行，因为已经作为章节名处理
        else:
            # 非空行，添加到当前章节内容
            current_content.append(line)
    
    # 保存最后一个章节
    if current_chapter is not None and current_content:
        chapters.append({
            'name': current_chapter,
            'content': '\n'.join(current_content).strip()
        })
    
    # 如果没有解析到任何章节，将整个内容作为一个章节
    if not chapters and content.strip():
        chapters.append({
            'name': '正文',
            'content': content.strip()
        })
    
    return chapters

@app.route('/api/novels/<novel_name>/chapters', methods=['GET'])
@login_required
def get_novel_chapters(novel_name):
    """获取小说的章节列表"""
    try:
        # 安全检查：防止目录遍历攻击
        safe_name = os.path.basename(novel_name)
        file_path = os.path.join(NOVELS_DIR, f"{safe_name}.txt")
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': '小说不存在'
            }), 404
        
        # 读取小说内容
        content = read_file_with_encoding(file_path)
        
        # 解析章节
        chapters = parse_chapters(content)
        
        # 只返回章节名称列表，不返回内容
        chapter_list = [{'index': i, 'name': ch['name']} for i, ch in enumerate(chapters)]
        
        return jsonify({
            'success': True,
            'chapters': chapter_list
        })
    except Exception as e:
        print(f"获取章节列表失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/novels/<novel_name>/chapters/<int:chapter_index>', methods=['GET'])
@login_required
def get_chapter_content(novel_name, chapter_index):
    """获取指定章节的内容"""
    try:
        # 安全检查：防止目录遍历攻击
        safe_name = os.path.basename(novel_name)
        file_path = os.path.join(NOVELS_DIR, f"{safe_name}.txt")
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': '小说不存在'
            }), 404
        
        # 读取小说内容
        content = read_file_with_encoding(file_path)
        
        # 解析章节
        chapters = parse_chapters(content)
        
        if chapter_index < 0 or chapter_index >= len(chapters):
            return jsonify({
                'success': False,
                'error': '章节不存在'
            }), 404
        
        chapter = chapters[chapter_index]
        
        return jsonify({
            'success': True,
            'chapter_name': chapter['name'],
            'content': chapter['content'],
            'chapter_index': chapter_index,
            'total_chapters': len(chapters)
        })
    except Exception as e:
        print(f"获取章节内容失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/board/chat-test/<room_name>')
@login_required
def chat_test(room_name):
    # 获取聊天室信息
    chat_room = ChatRoom.query.filter_by(name=room_name, is_active=True).first()
    if not chat_room:
        return redirect(url_for('chat'))
    return render_template('chat-simple.html', 
                         username=current_user.username, 
                         passkey_used=current_user.passkey_used,
                         room=chat_room, 
                         is_admin=current_user.is_admin, 
                         is_super_admin=current_user.is_super_admin)

@app.route('/api/chatrooms', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def manage_chatrooms():
    if request.method == 'GET':
        # 获取所有活跃的聊天室
        chat_rooms = ChatRoom.query.filter_by(is_active=True).all()
        return jsonify([{
            'id': room.id,
            'name': room.name,
            'has_password': bool(room.password),
            'created_by': room.created_by,
            'creator': User.query.get(room.created_by).username if room.created_by else '未知',
            'created_at': room.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_owner': room.created_by == current_user.id
        } for room in chat_rooms])
    
    elif request.method == 'POST':
        # 创建新聊天室
        data = request.json
        name = data['name']
        password = data.get('password')
        
        # 验证聊天室名称
        if not re.match(r'^[\w\u4e00-\u9fa5]+$', name):
            return jsonify({'error': '聊天室名称只能包含中文、英文或数字'}), 400
        
        # 检查名称是否已存在
        existing_room = ChatRoom.query.filter_by(name=name).first()
        if existing_room:
            return jsonify({'error': '聊天室名称已存在'}), 400
        
        # 创建聊天室
        chat_room = ChatRoom(
            name=name,
            created_by=current_user.id
        )
        
        if password:
            chat_room.password = generate_password_hash(password)
        
        db.session.add(chat_room)
        db.session.commit()
        
        return jsonify({
            'id': chat_room.id,
            'name': chat_room.name,
            'has_password': bool(chat_room.password),
            'created_by': chat_room.created_by,
            'creator': current_user.username,
            'created_at': chat_room.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_owner': True
        })
    
    elif request.method == 'PUT':
        # 编辑聊天室
        data = request.json
        room_id = data['id']
        name = data['name']
        password = data.get('password')
        
        # 获取聊天室
        chat_room = ChatRoom.query.get(room_id)
        if not chat_room or not chat_room.is_active:
            return jsonify({'error': '聊天室不存在或已关闭'}), 404
        
        # 只有创建者或管理员可以编辑
        if chat_room.created_by != current_user.id and not current_user.is_admin:
            return jsonify({'error': '权限不足'}), 403
        
        # 验证聊天室名称
        if not re.match(r'^[\w\u4e00-\u9fa5]+$', name):
            return jsonify({'error': '聊天室名称只能包含中文、英文或数字'}), 400
        
        # 检查名称是否已存在（排除当前聊天室）
        existing_room = ChatRoom.query.filter_by(name=name).filter(ChatRoom.id != room_id).first()
        if existing_room:
            return jsonify({'error': '聊天室名称已存在'}), 400
        
        # 更新聊天室信息
        chat_room.name = name
        if password:
            chat_room.password = generate_password_hash(password)
        elif password == '':
            # 清空密码
            chat_room.password = None
        
        db.session.commit()
        
        return jsonify({
            'id': chat_room.id,
            'name': chat_room.name,
            'has_password': bool(chat_room.password),
            'created_by': chat_room.created_by,
            'creator': User.query.get(chat_room.created_by).username if chat_room.created_by else '未知',
            'created_at': chat_room.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_owner': chat_room.created_by == current_user.id
        })
    
    elif request.method == 'DELETE':
        # 删除聊天室
        data = request.json
        room_id = data['id']
        chat_room = ChatRoom.query.get(room_id)
        if not chat_room:
            return jsonify({'error': '聊天室不存在'}), 404
        
        # 只有创建者或管理员可以删除
        if chat_room.created_by != current_user.id and not current_user.is_admin:
            return jsonify({'error': '权限不足'}), 403
        
        chat_room.is_active = False
        db.session.commit()
        return jsonify({'success': True})

# 处理DELETE请求到/api/chatrooms/{roomId}
@app.route('/api/chatrooms/<int:room_id>', methods=['DELETE'])
@login_required
def delete_chatroom(room_id):
    # 删除聊天室
    chat_room = ChatRoom.query.get(room_id)
    if not chat_room:
        return jsonify({'error': '聊天室不存在'}), 404
    
    # 只有创建者或管理员可以删除
    if chat_room.created_by != current_user.id and not current_user.is_admin:
        return jsonify({'error': '权限不足'}), 403
    
    chat_room.is_active = False
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/chatroom/join', methods=['POST'])
@login_required
def join_chatroom():
    data = request.json
    room_id = data['room_id']
    password = data.get('password')
    
    # 获取聊天室
    chat_room = ChatRoom.query.get(room_id)
    if not chat_room or not chat_room.is_active:
        return jsonify({'error': '聊天室不存在或已关闭'}), 404
    
    # 检查密码
    if chat_room.password:
        # 超级管理员和管理员可以直接进入
        if not current_user.is_super_admin and not current_user.is_admin:
            if not password or not check_password_hash(chat_room.password, password):
                return jsonify({'error': '密码错误'}), 401
    
    return jsonify({
        'success': True,
        'room_name': chat_room.name
    })

# 表情包管理API
@app.route('/api/stickers/hub', methods=['GET'])
@login_required
def get_sticker_hub():
    """获取表情包商城的公开表情列表"""
    try:
        sticker_type = request.args.get('type', 'single')  # 'single' 或 'pack'
        page = request.args.get('page', 1, type=int)
        
        if sticker_type == 'single':
            # 获取单个表情列表
            response = requests.get(f'{STICKER_API_BASE}/stickerhub', timeout=10)
        else:
            # 获取表情合集列表
            response = requests.get(f'{STICKER_API_BASE}/stickerpackhub', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'success': True,
                'data': data,
                'type': sticker_type
            })
        else:
            return jsonify({'success': False, 'error': '获取表情包列表失败'}), 500
    except Exception as e:
        print(f"获取表情包列表失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stickers/mine', methods=['GET'])
@login_required
def get_my_stickers():
    """获取当前用户的表情包列表"""
    try:
        sticker_type = request.args.get('type', 'single')
        stickers = UserSticker.query.filter_by(
            user_id=current_user.id,
            sticker_type=sticker_type
        ).all()
        
        return jsonify({
            'success': True,
            'data': [{
                'id': s.id,
                'code': s.sticker_code,
                'name': s.sticker_name,
                'description': s.description,
                'local_path': s.local_path,
                'created_at': s.created_at.strftime('%Y-%m-%d %H:%M:%S')
            } for s in stickers]
        })
    except Exception as e:
        print(f"获取用户表情包失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stickers/add', methods=['POST'])
@login_required
def add_sticker():
    """添加表情包到用户收藏"""
    try:
        data = request.json
        sticker_code = data.get('code')
        sticker_type = data.get('type', 'single')  # 'single' 或 'pack'
        
        if not sticker_code:
            return jsonify({'success': False, 'error': '请提供表情码'}), 400
        
        # 检查用户是否已添加此表情
        existing = UserSticker.query.filter_by(
            user_id=current_user.id,
            sticker_code=sticker_code
        ).first()
        
        if existing:
            return jsonify({'success': False, 'error': '您已经添加过这个表情了'}), 400
        
        # 从表情包服务器获取表情信息
        if sticker_type == 'single':
            response = requests.post(
                f'{STICKER_API_BASE}/getsticker',
                json={'code': sticker_code},
                timeout=10
            )
        else:
            response = requests.get(
                f'{STICKER_API_BASE}/getstickerpack',
                params={'code': sticker_code},
                timeout=10
            )
        
        if response.status_code != 200:
            return jsonify({'success': False, 'error': '获取表情信息失败'}), 500
        
        sticker_info = response.json()
        if not sticker_info.get('success'):
            return jsonify({'success': False, 'error': '表情不存在'}), 404
        
        # 下载并缓存表情图片
        if sticker_type == 'single':
            sticker_data = sticker_info
            image_url = sticker_data.get('url', '')
            sticker_name = sticker_data.get('description', '未命名表情')
            description = sticker_data.get('description', '')
        else:
            sticker_data = sticker_info.get('pack', {})
            image_url = sticker_data.get('cover_url', '')
            sticker_name = sticker_data.get('name', '未命名合集')
            description = sticker_data.get('description', '')
        
        # 下载图片
        local_path = download_sticker_image(image_url, sticker_code, sticker_type)
        
        if not local_path:
            return jsonify({'success': False, 'error': '下载表情图片失败'}), 500
        
        # 保存到数据库
        user_sticker = UserSticker(
            user_id=current_user.id,
            sticker_code=sticker_code,
            sticker_type=sticker_type,
            sticker_name=sticker_name,
            description=description,
            local_path=local_path
        )
        db.session.add(user_sticker)
        
        # 如果是表情包合集，下载合集中的所有表情
        if sticker_type == 'pack':
            stickers = sticker_data.get('stickers', [])
            print(f"开始下载表情包合集中的 {len(stickers)} 个表情")
            
            for i, sticker in enumerate(stickers):
                try:
                    item_code = sticker.get('code')
                    item_url = sticker.get('url')
                    
                    if not item_code and item_url:
                        # 为没有code的表情生成基于URL的唯一标识符
                        import hashlib
                        item_code = 'url_' + hashlib.md5(item_url.encode()).hexdigest()[:8]
                        print(f"为表情生成code: {item_code}")
                    
                    if item_code and item_url:
                        # 检查该合集中是否已经有这个表情
                        existing_sticker = PackSticker.query.filter_by(
                            user_id=current_user.id,
                            pack_code=sticker_code,
                            sticker_code=item_code
                        ).first()
                        
                        if not existing_sticker:
                            # 下载表情图片
                            local_sticker_path = download_sticker_image(
                                item_url, 
                                f"{sticker_code}_{item_code}", 
                                'pack_item'
                            )
                            
                            if local_sticker_path:
                                # 保存到PackSticker数据库（不是UserSticker）
                                try:
                                    pack_sticker = PackSticker(
                                        user_id=current_user.id,
                                        pack_code=sticker_code,
                                        sticker_code=item_code,
                                        sticker_name=sticker.get('description', '未命名表情'),
                                        description=sticker.get('description', ''),
                                        local_path=local_sticker_path
                                    )
                                    db.session.add(pack_sticker)
                                    print(f"下载并保存表情 {i+1}/{len(stickers)}: {item_code}")
                                except Exception as db_error:
                                    print(f"保存表情失败 {item_code}: {db_error}")
                                    # 回滚当前表情的添加，继续处理其他表情
                                    db.session.rollback()
                                    continue
                        else:
                            print(f"表情已存在，跳过: {item_code}")
                except Exception as e:
                    print(f"下载表情失败 {sticker.get('code', '未知')}: {e}")
                    continue
        
        # 提交所有保存
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '添加成功',
            'data': {
                'id': user_sticker.id,
                'code': sticker_code,
                'name': sticker_name,
                'description': description,
                'local_path': local_path
            }
        })
    except Exception as e:
        print(f"添加表情包失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stickers/remove', methods=['POST'])
@login_required
def remove_sticker():
    """从用户收藏中移除表情包"""
    try:
        data = request.json
        sticker_id = data.get('id')
        
        sticker = UserSticker.query.filter_by(
            id=sticker_id,
            user_id=current_user.id
        ).first()
        
        if not sticker:
            return jsonify({'success': False, 'error': '表情不存在'}), 404
        
        # 删除本地文件
        if os.path.exists(sticker.local_path):
            try:
                os.remove(sticker.local_path)
            except:
                pass
        
        db.session.delete(sticker)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '移除成功'})
    except Exception as e:
        print(f"移除表情包失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stickers/categories', methods=['GET'])
@login_required
def get_sticker_categories():
    """获取用户的表情包分类（用于聊天界面表情选择器）"""
    try:
        print(f"获取用户 {current_user.id} 的表情包分类")
        
        # 获取用户的所有表情包
        single_stickers = UserSticker.query.filter_by(
            user_id=current_user.id,
            sticker_type='single'
        ).all()
        
        pack_stickers = UserSticker.query.filter_by(
            user_id=current_user.id,
            sticker_type='pack'
        ).all()
        
        print(f"单个表情数量: {len(single_stickers)}, 表情包合集数量: {len(pack_stickers)}")
        
        # 构建分类数据
        categories = []
        
        # 单个表情分类 (C1位置)
        if single_stickers:
            single_category = {
                'id': 'single',
                'name': '单个表情',
                'type': 'single',
                'icon': 'favorite',  # Material Design爱心图标
                'stickers': []
            }
            for s in single_stickers:
                try:
                    single_category['stickers'].append({
                        'id': s.id,
                        'code': s.sticker_code,
                        'name': s.sticker_name or '未命名',
                        'local_path': s.local_path
                    })
                except Exception as sticker_error:
                    print(f"处理单个表情失败 {s.id}: {sticker_error}")
                    continue
            categories.append(single_category)
        
        # 表情包合集分类 (C2, C3, C4...位置)
        for pack in pack_stickers:
            try:
                categories.append({
                    'id': f'pack_{pack.id}',
                    'name': pack.sticker_name or '未命名合集',
                    'type': 'pack',
                    'code': pack.sticker_code,
                    'icon': pack.local_path,  # 使用封面作为图标
                    'stickers': []  # 需要在客户端通过code获取详情
                })
            except Exception as pack_error:
                print(f"处理表情包合集失败 {pack.id}: {pack_error}")
                continue
        
        print(f"返回分类数量: {len(categories)}")
        
        return jsonify({
            'success': True,
            'data': categories
        })
    except Exception as e:
        import traceback
        print(f"获取表情包分类失败: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stickers/pack/<code>', methods=['GET'])
@login_required
def get_pack_stickers(code):
    """获取表情包合集中的所有表情"""
    try:
        print(f"获取表情合集详情: {code}")
        
        # 首先检查用户是否拥有此合集
        user_pack = UserSticker.query.filter_by(
            user_id=current_user.id,
            sticker_code=code,
            sticker_type='pack'
        ).first()
        
        if not user_pack:
            print(f"用户未添加此表情包合集: {code}")
            return jsonify({'success': False, 'error': '您未添加此表情包合集'}), 404
        
        # 从表情包服务器获取合集详情
        try:
            response = requests.get(
                f'{STICKER_API_BASE}/getstickerpack',
                params={'code': code},
                timeout=10
            )
        except requests.RequestException as req_error:
            print(f"请求表情包服务器失败: {req_error}")
            return jsonify({'success': False, 'error': '无法连接到表情包服务器'}), 503
        
        if response.status_code == 200:
            try:
                data = response.json()
            except ValueError as json_error:
                print(f"解析JSON失败: {json_error}")
                return jsonify({'success': False, 'error': '服务器返回数据格式错误'}), 500
            
            if data.get('success') and data.get('pack'):
                pack = data['pack']
                stickers = pack.get('stickers', [])
                
                print(f"获取到 {len(stickers)} 个表情")
                
                # 从PackSticker表中获取已缓存的表情
                pack_stickers = PackSticker.query.filter_by(
                    user_id=current_user.id,
                    pack_code=code
                ).all()
                
                # 构建code到本地路径的映射
                pack_sticker_map = {ps.sticker_code: ps.local_path for ps in pack_stickers}
                print(f"找到 {len(pack_stickers)} 个已缓存的表情")
                
                # 为每个表情添加本地缓存路径（如果已缓存）
                processed_stickers = []
                for sticker in stickers:
                    try:
                        sticker_code = sticker.get('code')
                        sticker_url = sticker.get('url')
                        
                        if not sticker_code and sticker_url:
                            # 为没有code的表情生成基于URL的唯一标识符
                            import hashlib
                            sticker_code = 'url_' + hashlib.md5(sticker_url.encode()).hexdigest()[:8]
                        
                        local_path = pack_sticker_map.get(sticker_code)
                        
                        processed_sticker = {
                            'code': sticker_code,
                            'description': sticker.get('description', ''),
                            'url': sticker.get('url', ''),
                            'local_path': local_path,
                            'is_from_pack': True
                        }
                        processed_stickers.append(processed_sticker)
                    except Exception as sticker_error:
                        print(f"处理表情失败: {sticker_error}")
                        continue
                
                return jsonify({
                    'success': True,
                    'data': processed_stickers,
                    'pack_name': pack.get('name', '未命名合集'),
                    'pack_code': code
                })
            else:
                error_msg = data.get('error', '表情合集不存在')
                print(f"表情包服务器返回错误: {error_msg}")
                return jsonify({'success': False, 'error': error_msg}), 404
        else:
            print(f"表情包服务器返回状态码: {response.status_code}")
            return jsonify({'success': False, 'error': f'获取表情合集失败，状态码: {response.status_code}'}), 500
    except Exception as e:
        import traceback
        print(f"获取表情合集详情失败: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/stickers/<path:filename>')
@login_required
def serve_sticker(filename):
    """提供表情包图片服务"""
    return send_from_directory(STICKERS_DIR, filename)

def download_sticker_image(url, code, sticker_type):
    """下载并缓存表情图片"""
    try:
        # 构建完整的URL
        if url.startswith('/'):
            url = f'http://45.207.204.145:5003{url}'
        
        # 下载图片
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print(f"下载图片失败: {url}, 状态码: {response.status_code}")
            return None
        
        # 确定文件扩展名
        content_type = response.headers.get('content-type', '')
        if 'png' in content_type:
            ext = 'png'
        elif 'jpg' in content_type or 'jpeg' in content_type:
            ext = 'jpg'
        elif 'gif' in content_type:
            ext = 'gif'
        else:
            ext = 'png'  # 默认使用png
        
        # 构建文件名和路径
        filename = f"{sticker_type}_{code}.{ext}"
        filepath = os.path.join(STICKERS_DIR, filename)
        
        # 保存文件
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return f'/stickers/{filename}'
    except Exception as e:
        print(f"下载表情图片失败: {e}")
        return None

# 初始化数据库
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5002, debug=False)
