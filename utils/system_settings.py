import threading
from config import get_config, save_config

DEFAULT_SETTINGS = {
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

_settings_cache = None
_settings_lock = threading.Lock()

def get_settings():
    global _settings_cache
    
    with _settings_lock:
        if _settings_cache is not None:
            return _settings_cache.copy()
        
        config = get_config()
        settings = config.get('system_settings', {})
        
        for key, value in DEFAULT_SETTINGS.items():
            if key not in settings:
                settings[key] = value
        
        _settings_cache = settings
        return settings.copy()

def update_settings(new_settings):
    global _settings_cache
    
    with _settings_lock:
        config = get_config()
        
        if 'system_settings' not in config:
            config['system_settings'] = {}
        
        config['system_settings'].update(new_settings)
        
        save_config(config)
        
        _settings_cache = config['system_settings'].copy()
        
        return _settings_cache.copy()

def get_setting(key, default=None):
    settings = get_settings()
    return settings.get(key, default)

def set_setting(key, value):
    return update_settings({key: value})

def reset_settings():
    global _settings_cache
    
    with _settings_lock:
        config = get_config()
        config['system_settings'] = DEFAULT_SETTINGS.copy()
        save_config(config)
        
        _settings_cache = DEFAULT_SETTINGS.copy()
        
        return DEFAULT_SETTINGS.copy()

def init_settings():
    get_settings()
    print("系统设置初始化完成")
