import os
import mimetypes
from flask import jsonify, request, Response
from flask_login import login_required
from config import Config
from . import video_bp

VIDEOS_DIR = os.path.join(Config.INSTANCE_DIR, 'videos')

VIDEO_EXTENSIONS = {'.mp4', '.webm', '.ogg', '.ogv', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.m4v', '.mpg', '.mpeg', '.ts'}

def _ensure_videos_dir():
    if not os.path.exists(VIDEOS_DIR):
        os.makedirs(VIDEOS_DIR)

def _get_video_files():
    _ensure_videos_dir()
    videos = []
    try:
        for filename in os.listdir(VIDEOS_DIR):
            ext = os.path.splitext(filename)[1].lower()
            if ext in VIDEO_EXTENSIONS:
                filepath = os.path.join(VIDEOS_DIR, filename)
                size = os.path.getsize(filepath)
                videos.append({
                    'name': filename,
                    'size': size,
                    'size_display': _format_size(size)
                })
    except Exception as e:
        print(f"[Video] 扫描视频目录失败: {e}")
    videos.sort(key=lambda x: x['name'].lower())
    return videos

def _format_size(size):
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"

@video_bp.route('/api/videos')
@login_required
def list_videos():
    videos = _get_video_files()
    return jsonify(videos)

@video_bp.route('/api/video/<path:filename>')
@login_required
def stream_video(filename):
    filename = os.path.basename(filename)
    filepath = os.path.join(VIDEOS_DIR, filename)

    if not os.path.exists(filepath):
        return jsonify({'error': '视频文件不存在'}), 404

    file_size = os.path.getsize(filepath)
    mime_type, _ = mimetypes.guess_type(filepath)
    if not mime_type:
        ext = os.path.splitext(filename)[1].lower()
        mime_map = {
            '.mp4': 'video/mp4',
            '.webm': 'video/webm',
            '.ogg': 'video/ogg',
            '.ogv': 'video/ogg',
            '.mkv': 'video/x-matroska',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.wmv': 'video/x-ms-wmv',
            '.flv': 'video/x-flv',
            '.m4v': 'video/mp4',
            '.mpg': 'video/mpeg',
            '.mpeg': 'video/mpeg',
            '.ts': 'video/mp2t',
        }
        mime_type = mime_map.get(ext, 'application/octet-stream')

    range_header = request.headers.get('Range', None)

    if range_header:
        byte_range = range_header.replace('bytes=', '').split('-')
        start = int(byte_range[0]) if byte_range[0] else 0
        end = int(byte_range[1]) if len(byte_range) > 1 and byte_range[1] else file_size - 1

        if start >= file_size:
            return Response(status=416)

        end = min(end, file_size - 1)
        length = end - start + 1

        def generate():
            with open(filepath, 'rb') as f:
                f.seek(start)
                remaining = length
                chunk_size = 8192
                while remaining > 0:
                    chunk = f.read(min(chunk_size, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk

        response = Response(generate(), 206, mimetype=mime_type,
                          direct_passthrough=True)
        response.headers.add('Content-Range', f'bytes {start}-{end}/{file_size}')
        response.headers.add('Accept-Ranges', 'bytes')
        response.headers.add('Content-Length', str(length))
        return response

    def generate():
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                yield chunk

    response = Response(generate(), 200, mimetype=mime_type,
                      direct_passthrough=True)
    response.headers.add('Accept-Ranges', 'bytes')
    response.headers.add('Content-Length', str(file_size))
    return response
