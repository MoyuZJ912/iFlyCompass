import os
import platform
import shutil
import subprocess
import sys
import tarfile
import urllib.request

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TOOLS_DIR = os.path.join(PROJECT_ROOT, 'tools', 'ffmpeg')

LINUX_STATIC_URL = 'https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz'

_ffmpeg_path = None
_ffprobe_path = None


def _get_platform():
    return platform.system()


def _bundled_ffmpeg_path():
    system = _get_platform()
    if system == 'Windows':
        return os.path.join(TOOLS_DIR, 'ffmpeg.exe')
    return os.path.join(TOOLS_DIR, 'ffmpeg')


def _bundled_ffprobe_path():
    system = _get_platform()
    if system == 'Windows':
        return os.path.join(TOOLS_DIR, 'ffprobe.exe')
    return os.path.join(TOOLS_DIR, 'ffprobe')


def _is_executable(path):
    return os.path.exists(path) and os.access(path, os.X_OK)


def get_ffmpeg_path():
    global _ffmpeg_path
    if _ffmpeg_path:
        return _ffmpeg_path

    # 1. Try bundled binary
    bundled = _bundled_ffmpeg_path()
    if _is_executable(bundled):
        _ffmpeg_path = bundled
        return _ffmpeg_path

    # 2. Fall back to system PATH
    system_ffmpeg = shutil.which('ffmpeg')
    if system_ffmpeg:
        _ffmpeg_path = system_ffmpeg
        return _ffmpeg_path

    return None


def get_ffprobe_path():
    global _ffprobe_path
    if _ffprobe_path:
        return _ffprobe_path

    bundled = _bundled_ffprobe_path()
    if _is_executable(bundled):
        _ffprobe_path = bundled
        return _ffprobe_path

    system_ffprobe = shutil.which('ffprobe')
    if system_ffprobe:
        _ffprobe_path = system_ffprobe
        return _ffprobe_path

    return None


def verify_ffmpeg(path):
    try:
        result = subprocess.run([path, '-version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0].strip() if result.stdout else ''
            return True, version
        return False, ''
    except Exception as e:
        return False, str(e)


def _download_ffmpeg_linux():
    os.makedirs(TOOLS_DIR, exist_ok=True)

    archive_path = os.path.join(TOOLS_DIR, 'ffmpeg.tar.xz')
    print(f'[FFmpeg] 正在下载 Linux 静态构建 (约40MB)...')
    print(f'[FFmpeg] 源: {LINUX_STATIC_URL}')

    try:
        urllib.request.urlretrieve(LINUX_STATIC_URL, archive_path)
    except Exception as e:
        print(f'[FFmpeg] 下载失败: {e}')
        return None

    print(f'[FFmpeg] 下载完成，正在解压...')

    try:
        with tarfile.open(archive_path, 'r:xz') as tar:
            # Find the extraction root directory
            root_dir = None
            ffmpeg_member = None
            ffprobe_member = None

            for member in tar.getmembers():
                name = member.name
                if root_dir is None and '/' in name:
                    root_dir = name.split('/')[0]
                if name.endswith('/ffmpeg') and not name.endswith('/ffmpeg\\n'):
                    ffmpeg_member = member
                elif name.endswith('/ffprobe') and not name.endswith('/ffprobe\\n'):
                    ffprobe_member = member

            if ffmpeg_member:
                # Extract ffmpeg
                ffmpeg_member.name = 'ffmpeg'
                tar.extract(ffmpeg_member, TOOLS_DIR)
                os.chmod(os.path.join(TOOLS_DIR, 'ffmpeg'), 0o755)
                print(f'[FFmpeg] 已提取 ffmpeg')

            if ffprobe_member:
                ffprobe_member.name = 'ffprobe'
                tar.extract(ffprobe_member, TOOLS_DIR)
                os.chmod(os.path.join(TOOLS_DIR, 'ffprobe'), 0o755)
                print(f'[FFmpeg] 已提取 ffprobe')

    except Exception as e:
        print(f'[FFmpeg] 解压失败: {e}')
        return None
    finally:
        if os.path.exists(archive_path):
            os.remove(archive_path)

    ffmpeg_path = os.path.join(TOOLS_DIR, 'ffmpeg')
    if _is_executable(ffmpeg_path):
        ok, version = verify_ffmpeg(ffmpeg_path)
        if ok:
            print(f'[FFmpeg] FFmpeg 已就绪: {version}')
            return ffmpeg_path
        else:
            print(f'[FFmpeg] FFmpeg 验证失败: {version}')

    return None


def ensure_ffmpeg():
    """Ensure FFmpeg is available. Auto-download on Linux if needed."""
    global _ffmpeg_path, _ffprobe_path

    path = get_ffmpeg_path()
    if path:
        ok, version = verify_ffmpeg(path)
        if ok:
            print(f'[FFmpeg] 路径: {path}')
            print(f'[FFmpeg] 版本: {version}')
            return path
        else:
            print(f'[FFmpeg] 验证失败: {version}，尝试其他方式...')

    system = _get_platform()

    if system in ('Linux', 'Darwin'):
        print(f'[FFmpeg] 系统未检测到 FFmpeg，尝试自动下载...')
        path = _download_ffmpeg_linux()
        if path:
            _ffmpeg_path = path
            _ffprobe_path = os.path.join(TOOLS_DIR, 'ffprobe')
            return path

    print('[FFmpeg] 警告: FFmpeg 未找到，B站视频转换功能将不可用')
    return None
