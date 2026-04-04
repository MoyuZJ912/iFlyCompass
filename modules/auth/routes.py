from flask import render_template, redirect, url_for, request, flash, session
from flask_login import login_user, current_user, logout_user, login_required
from extensions import db
from models.user import User, Passkey
from . import auth_bp

user_sessions = {}

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.board'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            session.permanent = True
            user_sessions[username] = request.cookies.get('session')
            return redirect(url_for('main.board'))
        else:
            flash('用户名或密码错误')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.board'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        passkey = request.form.get('passkey', '')
        
        is_first_user = User.query.count() == 0
        
        if not is_first_user:
            passkey_obj = Passkey.query.filter_by(key=passkey).first()
            if not passkey_obj or not passkey_obj.is_valid():
                flash('无效的Passkey')
                return redirect(url_for('auth.register'))
            
            passkey_obj.current_uses += 1
            if passkey_obj.max_uses and passkey_obj.current_uses >= passkey_obj.max_uses:
                passkey_obj.is_active = False
            db.session.commit()
        
        if password != confirm_password:
            flash('两次输入的密码不一致')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('auth.register'))
        
        user = User(
            username=username,
            is_super_admin=is_first_user,
            is_admin=is_first_user,
            passkey_used=passkey if not is_first_user else None
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功，请登录')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/board/users')
@login_required
def user_management():
    if not (current_user.is_admin or current_user.is_super_admin):
        flash('权限不足')
        return redirect(url_for('main.board'))
    
    users = User.query.all()
    return render_template('user_management.html', 
                         users=users,
                         current_user=current_user)

@auth_bp.route('/board/passkeys')
@login_required
def passkey_management():
    if not current_user.is_super_admin:
        flash('权限不足')
        return redirect(url_for('main.board'))
    
    passkeys = Passkey.query.all()
    return render_template('passkey_management.html', 
                         passkeys=passkeys,
                         current_user=current_user)
