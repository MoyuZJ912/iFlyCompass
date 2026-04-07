import os
import hashlib
import requests
import threading
from config import Config

NCM_API_BASE = 'http://wjysrv.moyuzj.cn:29996'

_music_cache = {}
_cache_lock = threading.Lock()

def get_cache_path(song_id, file_type='mp3'):
    cache_dir = os.path.join(Config.TEMP_DIR, 'music')
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    return os.path.join(cache_dir, f"{song_id}.{file_type}")

def get_cached_music(song_id):
    cache_path = get_cache_path(song_id)
    if os.path.exists(cache_path):
        return cache_path
    return None

def download_music(song_id, url):
    try:
        cache_path = get_cache_path(song_id)
        
        if os.path.exists(cache_path):
            return cache_path
        
        response = requests.get(url, timeout=60, stream=True)
        if response.status_code == 200:
            with open(cache_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return cache_path
        return None
    except Exception as e:
        print(f"下载音乐失败 {song_id}: {e}")
        return None

def download_image(url, filename):
    try:
        cache_dir = os.path.join(Config.TEMP_DIR, 'music', 'covers')
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        cache_path = os.path.join(cache_dir, filename)
        
        if os.path.exists(cache_path):
            return cache_path
        
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(cache_path, 'wb') as f:
                f.write(response.content)
            return cache_path
        return None
    except Exception as e:
        print(f"下载封面失败 {url}: {e}")
        return None

def ncm_search(keywords, limit=30, offset=0, search_type=1):
    try:
        url = f"{NCM_API_BASE}/search"
        params = {
            'keywords': keywords,
            'limit': limit,
            'offset': offset,
            'type': search_type
        }
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"搜索失败: {e}")
        return {'code': 500, 'error': str(e)}

def ncm_get_song_url(song_id):
    try:
        url = f"{NCM_API_BASE}/song/url"
        params = {'id': song_id}
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"获取歌曲URL失败: {e}")
        return {'code': 500, 'error': str(e)}

def ncm_get_song_detail(song_ids):
    try:
        url = f"{NCM_API_BASE}/song/detail"
        params = {'ids': ','.join(map(str, song_ids)) if isinstance(song_ids, list) else str(song_ids)}
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"获取歌曲详情失败: {e}")
        return {'code': 500, 'error': str(e)}

def ncm_get_lyric(song_id):
    try:
        url = f"{NCM_API_BASE}/lyric"
        params = {'id': song_id}
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"获取歌词失败: {e}")
        return {'code': 500, 'error': str(e)}

def ncm_get_personalized(limit=30):
    try:
        url = f"{NCM_API_BASE}/personalized"
        params = {'limit': limit}
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"获取推荐歌单失败: {e}")
        return {'code': 500, 'error': str(e)}

def ncm_get_personalized_newsong(limit=10):
    try:
        url = f"{NCM_API_BASE}/personalized/newsong"
        params = {'limit': limit}
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"获取推荐新歌失败: {e}")
        return {'code': 500, 'error': str(e)}

def ncm_get_playlist_detail(playlist_id):
    try:
        url = f"{NCM_API_BASE}/playlist/detail"
        params = {'id': playlist_id}
        response = requests.get(url, params=params, timeout=10)
        return response.json()
    except Exception as e:
        print(f"获取歌单详情失败: {e}")
        return {'code': 500, 'error': str(e)}

def ncm_get_hot_search():
    try:
        url = f"{NCM_API_BASE}/search/hot/detail"
        response = requests.get(url, timeout=10)
        return response.json()
    except Exception as e:
        print(f"获取热搜失败: {e}")
        return {'code': 500, 'error': str(e)}
