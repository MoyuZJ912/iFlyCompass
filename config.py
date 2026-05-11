import os
import secrets
import hashlib
import base64
import yaml
from datetime import timedelta
from cryptography.fernet import Fernet

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'instance', 'config.yml')

# ---- Encryption utilities for sensitive config values ----

_fernet = None

def _get_fernet():
    """Get or create a Fernet instance derived from the Flask SECRET_KEY."""
    global _fernet
    if _fernet is not None:
        return _fernet
    # Derive a 32-byte key from SECRET_KEY, then base64-urlsafe encode for Fernet
    secret = Config.SECRET_KEY
    if not secret:
        secret = secrets.token_hex(32)
        Config.SECRET_KEY = secret
    # Use SHA-256 to get consistent 32 bytes, then base64 encode
    derived = hashlib.sha256(secret.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(derived)
    _fernet = Fernet(fernet_key)
    return _fernet

def _is_encrypted(value):
    """Check if a value is already encrypted (prefixed with 'enc:')."""
    return isinstance(value, str) and value.startswith('enc:')

def encrypt_value(value):
    """Encrypt a string value. Returns 'enc:<base64>' prefixed string."""
    if not value:
        return value
    f = _get_fernet()
    encrypted = f.encrypt(value.encode())
    return 'enc:' + base64.urlsafe_b64encode(encrypted).decode()

def decrypt_value(value):
    """Decrypt an 'enc:<base64>' prefixed string. Returns plaintext.
    If value is not encrypted (no 'enc:' prefix), returns as-is for backward compatibility."""
    if not value:
        return value
    if not _is_encrypted(value):
        # Plaintext value — migrate: encrypt it on next save
        return value
    try:
        f = _get_fernet()
        encrypted = base64.urlsafe_b64decode(value[4:].encode())
        return f.decrypt(encrypted).decode()
    except Exception:
        # If decryption fails (e.g., secret key changed), return empty
        return ''

DEFAULT_CONFIG = {
    'flask': {
        'secret_key': None,
        'session_lifetime_days': 3650
    },
    'database': {
        'path': 'users.db'
    },
    'directories': {
        'temp': './temp',
        'assets': './assets',
        'stickers': './stickers',
        'novels': './instance/novels',
        'music_cache': './temp/music',
        'videos': './instance/videos'
    },
    'external_api': {
        'sticker_api': 'http://45.207.204.145:5003/api'
    },
    'chat': {
        'max_message_history': 20
    },
    'system_settings': {
        'home_display': 'nickname',
        'allow_nickname': True,
        'nickname_min_length': 2,
        'nickname_max_length': 20,
        'sidebar_default_expanded': False,
        'card_layout': '1x4',
        'username_manual_min': 3,
        'username_manual_max': 50,
        'username_register_min': 3,
        'username_register_max': 50,
        'password_strength': 1,
        'allow_weak_password': False,
        'allow_self_password_reset': False,
        'allow_change_password': True
    }
}

_config_cache = None

def _ensure_instance_dir():
    instance_dir = os.path.dirname(CONFIG_FILE)
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)

def _load_config():
    global _config_cache
    
    if _config_cache is not None:
        return _config_cache
    
    _ensure_instance_dir()
    
    if not os.path.exists(CONFIG_FILE):
        print("配置文件不存在，创建默认配置...")
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(DEFAULT_CONFIG, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        _config_cache = DEFAULT_CONFIG.copy()
        return _config_cache
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    for key, value in DEFAULT_CONFIG.items():
        if key not in config:
            config[key] = value
        elif isinstance(value, dict):
            for sub_key, sub_value in value.items():
                if sub_key not in config[key]:
                    config[key][sub_key] = sub_value
    
    _config_cache = config
    return _config_cache

def get_config():
    return _load_config()

def save_config(config):
    global _config_cache
    
    _ensure_instance_dir()
    
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
    
    # Persist auto-generated secret_key so encrypted values survive restarts
    if not flask_config.get('secret_key') and not os.environ.get('SECRET_KEY'):
        config['flask']['secret_key'] = Config.SECRET_KEY
        save_config(config)
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
    Config.VIDEOS_DIR = dirs.get('videos', './instance/videos')
    
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
    VIDEOS_DIR = None
    STICKER_API_BASE = None
    MAX_MESSAGE_HISTORY = None

_init_config()
