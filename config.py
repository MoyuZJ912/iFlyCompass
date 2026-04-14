import os
import secrets
import yaml
from datetime import timedelta

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'instance', 'config.yml')

_config_cache = None

def _load_config():
    global _config_cache
    
    if _config_cache is not None:
        return _config_cache
    
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"配置文件不存在: {CONFIG_FILE}")
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        _config_cache = yaml.safe_load(f)
    
    return _config_cache

def get_config():
    return _load_config()

def save_config(config):
    global _config_cache
    
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    _config_cache = config

def _init_config():
    config = get_config()
    
    flask_config = config.get('flask', {})
    db_config = config.get('database', {})
    dirs = config.get('directories', {})
    external = config.get('external_api', {})
    chat_config = config.get('chat', {})
    
    Config.SECRET_KEY = flask_config.get('secret_key') or os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    Config.PERMANENT_SESSION_LIFETIME = timedelta(days=flask_config.get('session_lifetime_days', 3650))
    
    Config.INSTANCE_DIR = os.path.join(os.path.dirname(__file__), 'instance')
    db_path = os.path.join(Config.INSTANCE_DIR, db_config.get('path', 'users.db'))
    Config.SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    Config.SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    Config.TEMP_DIR = dirs.get('temp', './temp')
    Config.ASSETS_DIR = dirs.get('assets', './assets')
    Config.STICKERS_DIR = dirs.get('stickers', './stickers')
    Config.NOVELS_DIR = dirs.get('novels', './instance/novels')
    Config.MUSIC_CACHE_DIR = dirs.get('music_cache', './temp/music')
    
    Config.STICKER_API_BASE = external.get('sticker_api', 'http://45.207.204.145:5003/api')
    
    Config.MAX_MESSAGE_HISTORY = chat_config.get('max_message_history', 20)

class Config:
    SECRET_KEY = None
    PERMANENT_SESSION_LIFETIME = None
    INSTANCE_DIR = None
    SQLALCHEMY_DATABASE_URI = None
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TEMP_DIR = None
    ASSETS_DIR = None
    STICKERS_DIR = None
    NOVELS_DIR = None
    MUSIC_CACHE_DIR = None
    STICKER_API_BASE = None
    MAX_MESSAGE_HISTORY = None

_init_config()
