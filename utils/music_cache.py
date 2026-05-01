import os
import hashlib
import requests
import threading
from config import Config

_music_cache = {}
_cache_lock = threading.Lock()

def get_cache_path(song_id, file_type='mp3'):
    cache_dir = Config.MUSIC_CACHE_DIR
    if not os.path.exists(cache_dir):
        print(f"[MusicCache] 创建缓存目录: {cache_dir}")
        os.makedirs(cache_dir)
    
    filename = f"{song_id}.{file_type}"
    return os.path.join(cache_dir, filename)

def is_cached(song_id, file_type='mp3'):
    cache_path = get_cache_path(song_id, file_type)
    exists = os.path.exists(cache_path)
    print(f"[MusicCache] 检查缓存: song_id={song_id}, exists={exists}")
    return exists

def get_cached_music(song_id):
    cache_path = get_cache_path(song_id)
    if os.path.exists(cache_path):
        file_size = os.path.getsize(cache_path)
        print(f"[MusicCache] 缓存命中: {cache_path}, 大小: {file_size} bytes")
        return cache_path
    print(f"[MusicCache] 缓存未命中: song_id={song_id}")
    return None

def cache_music(song_id, url, name='unknown'):
    try:
        print(f"[MusicCache] 开始缓存音乐: {name} (ID: {song_id})")
        cache_path = get_cache_path(song_id, 'mp3')
        
        if os.path.exists(cache_path):
            file_size = os.path.getsize(cache_path)
            print(f"[MusicCache] 文件已存在, 跳过下载: {cache_path}, 大小: {file_size} bytes")
            return cache_path
        
        print(f"[MusicCache] 下载URL: {url[:80]}...")
        
        response = requests.get(url, timeout=60, stream=True)
        print(f"[MusicCache] HTTP响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"[MusicCache] 下载失败: HTTP {response.status_code}")
            return None
        
        content_length = response.headers.get('content-length', 'unknown')
        print(f"[MusicCache] Content-Length: {content_length}")
        
        temp_path = cache_path + '.tmp'
        downloaded = 0
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
        
        print(f"[MusicCache] 下载完成, 总大小: {downloaded} bytes")
        
        os.rename(temp_path, cache_path)
        print(f"[MusicCache] 文件已保存: {cache_path}")
        
        return cache_path
    except requests.exceptions.Timeout:
        print(f"[MusicCache] 下载超时: {url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[MusicCache] 网络请求错误: {e}")
        return None
    except Exception as e:
        print(f"[MusicCache] 缓存失败: {type(e).__name__}: {e}")
        return None

def cache_cover(pic_url):
    try:
        if not pic_url:
            return None
        
        print(f"[MusicCache] 缓存封面: {pic_url[:60]}...")
        
        url_hash = hashlib.md5(pic_url.encode()).hexdigest()
        cache_dir = os.path.join(Config.MUSIC_CACHE_DIR, 'covers')
        if not os.path.exists(cache_dir):
            print(f"[MusicCache] 创建封面缓存目录: {cache_dir}")
            os.makedirs(cache_dir)
        
        ext = 'jpg'
        if '.png' in pic_url.lower():
            ext = 'png'
        
        cache_path = os.path.join(cache_dir, f"{url_hash}.{ext}")
        
        if os.path.exists(cache_path):
            print(f"[MusicCache] 封面已缓存: {cache_path}")
            return f"/music/cache/covers/{url_hash}.{ext}"
        
        response = requests.get(pic_url, timeout=30)
        if response.status_code != 200:
            print(f"[MusicCache] 封面下载失败: HTTP {response.status_code}")
            return None
        
        with open(cache_path, 'wb') as f:
            f.write(response.content)
        
        print(f"[MusicCache] 封面已保存: {cache_path}")
        return f"/music/cache/covers/{url_hash}.{ext}"
    except Exception as e:
        print(f"[MusicCache] 缓存封面失败: {e}")
        return None
