import os
import asyncio
import threading
import subprocess
from concurrent.futures import ThreadPoolExecutor
from config import Config

try:
    from bilibili_api import select_client
    select_client("curl_cffi")
except Exception as e:
    print(f'[Bili] 无法选择 curl_cffi: {e}')

BILI_DIR = os.path.join(Config.TEMP_DIR, 'bili') if Config.TEMP_DIR else os.path.join(os.path.dirname(__file__), '..', 'temp', 'bili')

FFMPEG_PATH = os.path.join(os.path.dirname(__file__), '..', 'tools', 'ffmpeg', 'ffmpeg.exe')
if not os.path.exists(FFMPEG_PATH):
    FFMPEG_PATH = 'ffmpeg'

QUALITY_MAP = {
    16: '360P',
    32: '480P',
    64: '720P',
    74: '720P60',
    80: '1080P',
    112: '1080P+',
    116: '1080P60',
    120: '4K',
}

DEFAULT_QUALITY = 32

download_tasks = {}
download_lock = threading.Lock()
executor = ThreadPoolExecutor(max_workers=3)


def ensure_bili_dir():
    if not os.path.exists(BILI_DIR):
        os.makedirs(BILI_DIR)


def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)


def get_video_info_sync(bvid):
    from bilibili_api import video
    
    async def _get_info():
        v = video.Video(bvid=bvid)
        info = await v.get_info()
        cid = info.get('cid', 0)
        if not cid and info.get('pages'):
            cid = info['pages'][0].get('cid', 0)
        return info, cid
    
    return run_async(_get_info())


def get_download_streams_sync(bvid, cid):
    from bilibili_api import video
    from bilibili_api.video import VideoDownloadURLDataDetecter, VideoQuality
    
    async def _get_streams():
        v = video.Video(bvid=bvid)
        url_data = await v.get_download_url(cid=cid)
        
        detecter = VideoDownloadURLDataDetecter(url_data)
        streams = detecter.detect_best_streams(
            video_max_quality=VideoQuality._480P,
            video_min_quality=VideoQuality._360P
        )
        return streams
    
    return run_async(_get_streams())


def get_video_cache_path(bvid):
    ensure_bili_dir()
    return os.path.join(BILI_DIR, f'{bvid}.mp4')


def is_video_cached(bvid):
    path = get_video_cache_path(bvid)
    return os.path.exists(path)


def get_cached_videos():
    ensure_bili_dir()
    videos = []
    try:
        for filename in os.listdir(BILI_DIR):
            if filename.endswith('.mp4'):
                bvid = filename[:-4]
                filepath = os.path.join(BILI_DIR, filename)
                size = os.path.getsize(filepath)
                videos.append({
                    'bvid': bvid,
                    'size': size,
                    'size_display': format_size(size)
                })
    except Exception as e:
        print(f'[Bili] 扫描缓存目录失败: {e}')
    return videos


def format_size(size):
    if size < 1024:
        return f'{size} B'
    elif size < 1024 * 1024:
        return f'{size / 1024:.1f} KB'
    elif size < 1024 * 1024 * 1024:
        return f'{size / (1024 * 1024):.1f} MB'
    else:
        return f'{size / (1024 * 1024 * 1024):.2f} GB'


class DownloadTask:
    def __init__(self, bvid, title, cid):
        self.bvid = bvid
        self.title = title
        self.cid = cid
        self.status = 'pending'
        self.progress = 0
        self.downloaded = 0
        self.total = 0
        self.speed = 0
        self.error = None
        self.start_time = None
        self.last_update = None
        self.last_downloaded = 0

    def to_dict(self):
        return {
            'bvid': self.bvid,
            'title': self.title,
            'status': self.status,
            'progress': self.progress,
            'downloaded': self.downloaded,
            'total': self.total,
            'downloaded_display': format_size(self.downloaded),
            'total_display': format_size(self.total),
            'speed': self.speed,
            'speed_display': format_size(self.speed) + '/s' if self.speed > 0 else '0 B/s',
            'error': self.error
        }


def download_file_with_progress(url, filepath, task, headers=None):
    import requests
    import time
    
    req_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com/',
    }
    if headers:
        req_headers.update(headers)
    
    resp = requests.get(url, headers=req_headers, stream=True, timeout=30)
    total_size = int(resp.headers.get('content-length', 0))
    
    downloaded = 0
    last_check = time.time()
    last_downloaded = 0
    
    with open(filepath, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                task.downloaded += len(chunk)
                
                now = time.time()
                if now - last_check >= 0.3:
                    elapsed = now - last_check
                    task.speed = int((downloaded - last_downloaded) / elapsed) if elapsed > 0 else 0
                    if task.total > 0:
                        task.progress = int(task.downloaded / task.total * 100)
                    last_check = now
                    last_downloaded = downloaded
    
    return downloaded


def merge_video_audio(video_path, audio_path, output_path):
    try:
        cmd = [
            FFMPEG_PATH, '-y',
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-strict', 'experimental',
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        if result.returncode != 0:
            print(f'[Bili] FFmpeg合并失败: {result.stderr.decode("utf-8", errors="ignore")}')
            return False
        return True
    except FileNotFoundError:
        print('[Bili] FFmpeg未找到，尝试直接合并')
        return False
    except Exception as e:
        print(f'[Bili] 合并异常: {e}')
        return False


def download_video_task(task):
    import requests
    import time
    from bilibili_api.video import VideoStreamDownloadURL, AudioStreamDownloadURL, FLVStreamDownloadURL, MP4StreamDownloadURL
    
    try:
        task.status = 'fetching'
        task.start_time = time.time()
        task.last_update = time.time()
        
        info, cid = get_video_info_sync(task.bvid)
        task.title = info.get('title', task.bvid)
        
        streams = get_download_streams_sync(task.bvid, cid)
        
        if not streams:
            raise Exception('未找到可用的下载流')
        
        video_path = get_video_cache_path(task.bvid)
        temp_video_path = video_path + '.video'
        temp_audio_path = video_path + '.audio'
        
        headers = {'Referer': 'https://www.bilibili.com/'}
        
        if len(streams) == 1 and isinstance(streams[0], (FLVStreamDownloadURL, MP4StreamDownloadURL)):
            stream = streams[0]
            url = stream.url
            task.total = 0
            task.status = 'downloading'
            download_file_with_progress(url, video_path, task, headers)
            task.status = 'completed'
            task.progress = 100
            
        elif len(streams) >= 2:
            video_stream = None
            audio_stream = None
            
            for s in streams:
                if isinstance(s, VideoStreamDownloadURL) and video_stream is None:
                    video_stream = s
                elif isinstance(s, AudioStreamDownloadURL) and audio_stream is None:
                    audio_stream = s
            
            if not video_stream:
                raise Exception('未找到视频流')
            
            video_url = video_stream.url
            audio_url = audio_stream.url if audio_stream else None
            
            task.total = 0
            task.status = 'downloading'
            
            download_file_with_progress(video_url, temp_video_path, task, headers)
            
            if audio_url:
                download_file_with_progress(audio_url, temp_audio_path, task, headers)
            
            task.status = 'merging'
            
            if audio_url and os.path.exists(temp_audio_path) and os.path.exists(temp_video_path):
                success = merge_video_audio(temp_video_path, temp_audio_path, video_path)
                if success:
                    try:
                        os.remove(temp_video_path)
                        os.remove(temp_audio_path)
                    except:
                        pass
                else:
                    if os.path.exists(temp_video_path):
                        os.rename(temp_video_path, video_path)
            else:
                if os.path.exists(temp_video_path):
                    os.rename(temp_video_path, video_path)
            
            task.status = 'completed'
            task.progress = 100
        else:
            raise Exception('未找到可用的下载地址')
            
    except Exception as e:
        task.status = 'error'
        task.error = str(e)
        print(f'[Bili] 下载失败 {task.bvid}: {e}')


def start_download(bvid):
    with download_lock:
        if bvid in download_tasks:
            task = download_tasks[bvid]
            if task.status in ['pending', 'downloading', 'fetching', 'merging']:
                return task
        
        if is_video_cached(bvid):
            return None
        
        try:
            info, cid = get_video_info_sync(bvid)
            title = info.get('title', bvid)
            
            task = DownloadTask(bvid, title, cid)
            download_tasks[bvid] = task
            
            executor.submit(download_video_task, task)
            
            return task
        except Exception as e:
            raise Exception(f'启动下载失败: {e}')


def get_download_progress(bvid):
    with download_lock:
        if bvid in download_tasks:
            return download_tasks[bvid].to_dict()
    return None


def get_all_downloads():
    with download_lock:
        return [task.to_dict() for task in download_tasks.values()]


def delete_cached_video(bvid):
    path = get_video_cache_path(bvid)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def get_video_info(bvid):
    info, cid = get_video_info_sync(bvid)
    return info
