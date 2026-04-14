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
from modules.chat.websocket import register_socketio_events
from utils import init_novel_cache, init_settings

for directory in [Config.TEMP_DIR, Config.INSTANCE_DIR, Config.STICKERS_DIR, Config.NOVELS_DIR]:
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
    
    register_socketio_events(socketio)
    
    with app.app_context():
        db.create_all()
        run_migrations(app)
    
    init_novel_cache()
    init_settings()
    
    return app

app = create_app()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5002, debug=False)
