import os
import sqlite3
from flask import Flask
from config import Config
from extensions import db, login_manager, socketio
from modules.auth import auth_bp
from modules.chat import chat_bp
from modules.novel import novel_bp
from modules.sticker import sticker_bp
from modules.main import main_bp
from modules.ncm import ncm_bp
from modules.settings import settings_bp
from modules.announcement import announcement_bp
from modules.drop import drop_bp
from modules.video import video_bp
from modules.bili import bili_bp
from modules.proxy import proxy_bp
from modules.chat.websocket import register_socketio_events
from utils import init_novel_cache, init_settings, init_nav_file

for directory in [Config.TEMP_DIR, Config.INSTANCE_DIR, Config.STICKERS_DIR, Config.NOVELS_DIR, Config.VIDEOS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

def run_migrations(app):
    db_path = os.path.join(Config.INSTANCE_DIR, 'users.db')
    
    if not os.path.exists(db_path):
        return
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'nickname' not in columns:
            print("正在迁移数据库：添加 nickname 字段...")
            cursor.execute("ALTER TABLE user ADD COLUMN nickname VARCHAR(50)")
            conn.commit()
            print("数据库迁移完成！")
        
        if 'security_question' not in columns:
            print("正在迁移数据库：添加 security_question 字段...")
            cursor.execute("ALTER TABLE user ADD COLUMN security_question VARCHAR(255)")
            conn.commit()
            print("数据库迁移完成！")
        
        if 'security_answer_hash' not in columns:
            print("正在迁移数据库：添加 security_answer_hash 字段...")
            cursor.execute("ALTER TABLE user ADD COLUMN security_answer_hash VARCHAR(128)")
            conn.commit()
            print("数据库迁移完成！")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='announcement'")
        if not cursor.fetchone():
            print("正在迁移数据库：创建 announcement 表...")
            cursor.execute('''
                CREATE TABLE announcement (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(200) NOT NULL,
                    content TEXT NOT NULL,
                    announcement_type VARCHAR(20) NOT NULL DEFAULT 'notification',
                    priority VARCHAR(20) NOT NULL DEFAULT 'normal',
                    created_by INTEGER NOT NULL,
                    created_at DATETIME,
                    updated_at DATETIME,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (created_by) REFERENCES user(id)
                )
            ''')
            conn.commit()
            print("数据库迁移完成！")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_announcement_status'")
        if not cursor.fetchone():
            print("正在迁移数据库：创建 user_announcement_status 表...")
            cursor.execute('''
                CREATE TABLE user_announcement_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    announcement_id INTEGER NOT NULL,
                    is_dismissed BOOLEAN DEFAULT 0,
                    dismissed_at DATETIME,
                    session_dismissed BOOLEAN DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES user(id),
                    FOREIGN KEY (announcement_id) REFERENCES announcement(id),
                    CONSTRAINT unique_user_announcement UNIQUE (user_id, announcement_id)
                )
            ''')
            conn.commit()
            print("数据库迁移完成！")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='drop_message'")
        if not cursor.fetchone():
            print("正在迁移数据库：创建 drop_message 表...")
            cursor.execute('''
                CREATE TABLE drop_message (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER NOT NULL,
                    sender_name VARCHAR(50) NOT NULL,
                    content VARCHAR(200) NOT NULL,
                    created_at DATETIME,
                    FOREIGN KEY (sender_id) REFERENCES user(id)
                )
            ''')
            conn.commit()
            print("数据库迁移完成！")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='drop_settings'")
        if not cursor.fetchone():
            print("正在迁移数据库：创建 drop_settings 表...")
            cursor.execute('''
                CREATE TABLE drop_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    enabled BOOLEAN DEFAULT 1,
                    last_drop_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES user(id)
                )
            ''')
            conn.commit()
            print("数据库迁移完成！")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='drop_blacklist'")
        if not cursor.fetchone():
            print("正在迁移数据库：创建 drop_blacklist 表...")
            cursor.execute('''
                CREATE TABLE drop_blacklist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    blocked_user_id INTEGER NOT NULL,
                    created_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES user(id),
                    FOREIGN KEY (blocked_user_id) REFERENCES user(id),
                    CONSTRAINT unique_blacklist UNIQUE (user_id, blocked_user_id)
                )
            ''')
            conn.commit()
            print("数据库迁移完成！")
        
        cursor.execute("PRAGMA table_info(chat_room)")
        chat_room_columns = [column[1] for column in cursor.fetchall()]
        
        if 'multi_user_mode' not in chat_room_columns:
            print("正在迁移数据库：添加 chat_room.multi_user_mode 字段...")
            cursor.execute("ALTER TABLE chat_room ADD COLUMN multi_user_mode BOOLEAN DEFAULT 0")
            conn.commit()
            print("数据库迁移完成！")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='video_access_control'")
        if not cursor.fetchone():
            print("正在迁移数据库：创建 video_access_control 表...")
            cursor.execute('''
                CREATE TABLE video_access_control (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_path VARCHAR(500) NOT NULL UNIQUE,
                    mode VARCHAR(20) NOT NULL DEFAULT 'public',
                    created_by INTEGER,
                    created_at DATETIME,
                    updated_at DATETIME,
                    FOREIGN KEY (created_by) REFERENCES user(id)
                )
            ''')
            conn.commit()
            print("数据库迁移完成！")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='video_access_user'")
        if not cursor.fetchone():
            print("正在迁移数据库：创建 video_access_user 表...")
            cursor.execute('''
                CREATE TABLE video_access_user (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_path VARCHAR(500) NOT NULL,
                    user_id INTEGER NOT NULL,
                    created_at DATETIME,
                    FOREIGN KEY (user_id) REFERENCES user(id),
                    CONSTRAINT unique_video_access_user UNIQUE (video_path, user_id)
                )
            ''')
            conn.commit()
            print("数据库迁移完成！")

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app, async_mode='threading')
    
    login_manager.login_view = 'auth.login'
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(novel_bp)
    app.register_blueprint(sticker_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(ncm_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(announcement_bp)
    app.register_blueprint(drop_bp)
    app.register_blueprint(video_bp)
    app.register_blueprint(bili_bp)
    app.register_blueprint(proxy_bp)
    
    register_socketio_events(socketio)
    
    with app.app_context():
        db.create_all()
        run_migrations(app)
    
    init_novel_cache()
    init_settings()
    init_nav_file()
    
    from modules.proxy.proxy_server import start_proxy_server
    start_proxy_server()
    
    return app

app = create_app()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5002, debug=False)
