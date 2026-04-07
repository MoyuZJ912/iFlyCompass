import os
import secrets
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    INSTANCE_DIR = './instance'
    db_path = os.path.join(os.path.abspath(INSTANCE_DIR), 'users.db')
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    PERMANENT_SESSION_LIFETIME = timedelta(days=365 * 10)
    
    TEMP_DIR = './temp'
    ASSETS_DIR = './assets'
    STICKERS_DIR = './stickers'
    NOVELS_DIR = './instance/novels'
    MUSIC_CACHE_DIR = './temp/music'
    
    STICKER_API_BASE = 'http://45.207.204.145:5003/api'
    
    MAX_MESSAGE_HISTORY = 20
