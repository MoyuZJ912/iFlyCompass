import socket
import subprocess
import sys
import os
import time
import signal

PROXY_PORT = 5003
_proxy_host = '127.0.0.1'
_proxy_process = None


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def _find_mitmdump():
    try:
        import subprocess
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tools_dir = os.path.join(base_dir, 'tools')
        if sys.platform == 'win32':
            mitmdump_path = os.path.join(tools_dir, 'mitmdump.exe')
        else:
            mitmdump_path = os.path.join(tools_dir, 'mitmdump')
        if os.path.isfile(mitmdump_path):
            return mitmdump_path
    except Exception:
        pass

    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'show', 'mitmproxy'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            location = None
            for line in result.stdout.splitlines():
                if line.startswith('Location:'):
                    location = line.split(':', 1)[1].strip()
                    break
            if location:
                scripts_dir = os.path.join(location, '..', 'Scripts')
                scripts_dir = os.path.normpath(scripts_dir)
                if sys.platform == 'win32':
                    mitmdump_path = os.path.join(scripts_dir, 'mitmdump.exe')
                else:
                    mitmdump_path = os.path.join(scripts_dir, 'mitmdump')
                if os.path.isfile(mitmdump_path):
                    return mitmdump_path
    except Exception:
        pass

    python_exe = sys.executable
    python_dir = os.path.dirname(python_exe)
    mitmdump_path = os.path.join(python_dir, 'mitmdump.exe' if sys.platform == 'win32' else 'mitmdump')
    if os.path.isfile(mitmdump_path):
        return mitmdump_path
    try:
        import shutil
        result = shutil.which('mitmdump')
        if result:
            return result
    except Exception:
        pass
    return None


def _update_addon_host():
    global _proxy_host
    addon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'proxy_addon.py')
    try:
        with open(addon_path, 'r', encoding='utf-8') as f:
            content = f.read()
        content = content.replace(
            "PROXY_HOST = '127.0.0.1'",
            "PROXY_HOST = '" + _proxy_host + "'"
        )
        with open(addon_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        print('[WebProxy] 更新 addon 脚本失败: ' + str(e))


def start_proxy_server(host='0.0.0.0', port=5003):
    global _proxy_host, _proxy_process

    _proxy_host = get_local_ip() or '127.0.0.1'

    if _proxy_process is not None and _proxy_process.poll() is None:
        return True

    try:
        import subprocess
        subprocess.run(['taskkill', '/F', '/IM', 'mitmdump.exe'], capture_output=True, timeout=5)
    except Exception:
        pass

    try:
        addon_dir = os.path.dirname(os.path.abspath(__file__))
        host_file = os.path.join(addon_dir, '.proxy_host')
        with open(host_file, 'w') as f:
            f.write(_proxy_host)
    except Exception:
        pass

    mitmdump = _find_mitmdump()
    if not mitmdump:
        print('[WebProxy] 未找到 mitmdump，请确保 mitmproxy 已安装')
        return False

    _update_addon_host()

    addon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'proxy_addon.py')

    cmd = [
        mitmdump,
        '--listen-host', host,
        '--listen-port', str(port),
        '--mode', 'regular',
        '--set', 'http2=false',
        '--set', 'ssl_insecure=true',
        '--set', 'console_eventlog_verbosity=error',
        '--set', 'termlog_verbosity=error',
        '-s', addon_path,
    ]

    try:
        _proxy_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        )

        time.sleep(1.5)

        if _proxy_process.poll() is not None:
            print('[WebProxy] mitmdump 进程启动后立即退出，退出码: ' + str(_proxy_process.returncode))
            _proxy_process = None
            return False

        print('[WebProxy] 代理服务器已启动 (mitmproxy): http://' + _proxy_host + ':' + str(port))
        return True
    except Exception as e:
        print('[WebProxy] 代理服务器启动失败: ' + str(e))
        _proxy_process = None
        return False


def stop_proxy_server():
    global _proxy_process
    if _proxy_process is not None:
        try:
            if sys.platform == 'win32':
                _proxy_process.terminate()
            else:
                _proxy_process.send_signal(signal.SIGTERM)
            try:
                _proxy_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                _proxy_process.kill()
                _proxy_process.wait(timeout=3)
        except Exception:
            try:
                _proxy_process.kill()
            except Exception:
                pass
        _proxy_process = None


def is_proxy_running():
    global _proxy_process
    if _proxy_process is None:
        return False
    return _proxy_process.poll() is None


def get_proxy_url():
    if not is_proxy_running():
        return None
    return 'http://' + _proxy_host + ':' + str(PROXY_PORT)


def get_proxy_host():
    return _proxy_host
