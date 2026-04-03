import os
import requests
import random
import string
from datetime import datetime, timezone, timedelta
from config import Config

def get_bing_wallpaper():
    try:
        bing_api_url = 'https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=zh-CN'
        response = requests.get(bing_api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('images'):
                image_url = 'https://www.bing.com' + data['images'][0]['url']
                image_response = requests.get(image_url, timeout=10)
                if image_response.status_code == 200:
                    wallpaper_path = os.path.join(Config.TEMP_DIR, 'bing_wallpaper.jpg')
                    with open(wallpaper_path, 'wb') as f:
                        f.write(image_response.content)
                    return '/temp/bing_wallpaper.jpg'
    except Exception as e:
        print(f"获取必应壁纸失败: {e}")
    return None

def get_poetry():
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
    characters = string.ascii_uppercase + string.digits
    while True:
        key = ''.join(random.choice(characters) for _ in range(6))
        from models.user import Passkey
        if not Passkey.query.filter_by(key=key).first():
            return key

def get_utc_plus_8_time():
    return datetime.now(timezone(timedelta(hours=8)))
