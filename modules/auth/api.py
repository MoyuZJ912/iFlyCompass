from flask import jsonify, request
from flask_login import login_required, current_user
from extensions import db
from models.user import User, Passkey
from utils import generate_passkey, get_utc_plus_8_time
from datetime import timedelta
from . import auth_bp

@auth_bp.route('/api/users', methods=['GET', 'POST', 'PUT', 'DELETE'])
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

@auth_bp.route('/api/passkeys', methods=['GET', 'POST', 'DELETE'])
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
        
        key = generate_passkey()
        
        expires_at = None
        if duration_days:
            expires_at = get_utc_plus_8_time() + timedelta(days=duration_days)
        
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
