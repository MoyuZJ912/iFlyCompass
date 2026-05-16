from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask import session

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()

@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    user = User.query.get(int(user_id))
    if user:
        session_version = session.get('_session_version')
        if session_version is not None and session_version != (user.session_version or 0):
            return None
    return user
