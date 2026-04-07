import os
import hashlib
import requests
import threading
from config import Config

_music_cache = {}
_cache_lock = threading.Lock()

NCM_API_BASE = 'http://wjysrv.moyuzj.cn:29996'

def get_cache_path(song_id, file_type='mp3'):
    cache_dir = Config.MUSIC_CACHE_DIR
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    filename = f"{song_id}.{file_type}"
    return os.path.join(cache_dir, filename)

def is_cached(song_id, file_type='mp3'):
    cache_path = get_cache_path(song_id, file_type)
    return os.path.exists(cache_path)

def get_cached_music(song_id):
    cache_path = get_cache_path(song_id)
    if os.path.exists(cache_path):
        return cache_path
    return None

def cache_music(song_id, url, name='unknown'):
    try:
        cache_path = get_cache_path(song_id, 'mp3')
        
        if os.path.exists(cache_path):
            return cache_path
        
        print(f"正在缓存音乐: {name} (ID: {song_id})")
        
        response = requests.get(url, timeout=60, stream=True)
        if response.status_code != 200:
            print(f"下载音乐失败: {url}, 状态码: {response.status_code}")
            return None
        
        temp_path = cache_path + '.tmp'
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        os.rename(temp_path, cache_path)
        
        print(f"音乐缓存完成: {name}")
        return cache_path
    except Exception as e:
        print(f"缓存音乐失败: {e}")
        return None

def cache_cover(pic_url):
    try:
        if not pic_url:
            return None
        
        url_hash = hashlib.md5(pic_url.encode()).hexdigest()
        cache_dir = os.path.join(Config.MUSIC_CACHE_DIR, 'covers')
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        ext = 'jpg'
        if '.png' in pic_url.lower():
            ext = 'png'
        
        cache_path = os.path.join(cache_dir, f"{url_hash}.{ext}")
        
        if os.path.exists(cache_path):
            return f"/music/cache/covers/{url_hash}.{ext}"
        
        response = requests.get(pic_url, timeout=30)
        if response.status_code != 200:
            return None
        
        with open(cache_path, 'wb') as f:
            f.write(response.content)
        
        return f"/music/cache/covers/{url_hash}.{ext}"
    except Exception as e:
        print(f"缓存封面失败: {e}")
        return None

def ncm_api_request(endpoint, params=None):
    try:
        url = f"{NCM_API_BASE}{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"NCM API请求失败: {endpoint}, {e}")
        return None

def search_songs(keywords, limit=30, offset=0):
    return ncm_api_request('/search', {
        'keywords': keywords,
        'limit': limit,
        'offset': offset,
        'type': 1
    })

def get_song_url(song_id):
    return ncm_api_request('/song/url', {'id': song_id})

def get_song_detail(song_ids):
    if isinstance(song_ids, list):
        song_ids = ','.join(map(str, song_ids))
    return ncm_api_request('/song/detail', {'ids': song_ids})

def get_personalized(limit=30):
    return ncm_api_request('/personalized', {'limit': limit})

def get_personalized_newsong(limit=10):
    return ncm_api_request('/personalized/newsong', {'limit': limit})

def get_lyric(song_id):
    return ncm_api_request('/lyric', {'id': song_id})

def get_hot_search():
    return ncm_api_request('/search/hot/detail')

def get_playlist_detail(playlist_id):
    return ncm_api_request('/playlist/detail', {'id': playlist_id})
