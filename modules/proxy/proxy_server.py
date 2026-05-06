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


def _get_local_mitmdump_path():
    """获取本地内置的 mitmproxy 路径"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    if sys.platform == "win32":
        mitmdump_exe = os.path.join(project_root, "tools", "mitmproxy", "mitmdump.exe")
        if os.path.isfile(mitmdump_exe):
            return mitmdump_exe
    
    mitmdump_unix = os.path.join(project_root, "tools", "mitmproxy", "mitmdump")
    if os.path.isfile(mitmdump_unix):
        return mitmdump_unix
    
    return None


def _find_mitmdump():
    """查找 mitmdump 可执行文件（优先使用本地内置版本）"""
    
    # 1. 优先使用项目内置的 mitmproxy
    local_mitmdump = _get_local_mitmdump_path()
    if local_mitmdump:
        print('[WebProxy] 使用本地内置 mitmproxy: ' + local_mitmdump)
        return local_mitmdump, True  # (路径, 是否为本地版本)
    
    # 2. 回退到系统安装的 mitmproxy（兼容旧环境）
    python_exe = sys.executable
    python_dir = os.path.dirname(python_exe)
    
    if sys.platform == "win32":
        candidates = [
            os.path.join(python_dir, 'mitmdump.exe'),
            os.path.join(python_dir, 'Scripts', 'mitmdump.exe'),
        ]
    else:
        candidates = [
            os.path.join(python_dir, 'bin', 'mitmdump'),
            os.path.join(python_dir, 'local', 'bin', 'mitmdump'),
        ]
    
    for candidate in candidates:
        if os.path.isfile(candidate):
            print('[WebProxy] 使用系统安装 mitmproxy: ' + candidate)
            return candidate, False
    
    try:
        import shutil
        result = shutil.which('mitmdump')
        if result:
            print('[WebProxy] 从 PATH 找到 mitmproxy: ' + result)
            return result, False
    except Exception:
        pass
    
    return None, False


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

    mitmdump_path, is_local = _find_mitmdump()
    if not mitmdump_path:
        print('[WebProxy] 未找到 mitmdump，请确保 mitmproxy 已安装或运行 python tools/install_mitmproxy.py')
        return False

    _update_addon_host()

    addon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'proxy_addon.py')

    cmd = [
        mitmdump_path,
        '--listen-host', host,
        '--listen-port', str(port),
        '--mode', 'regular',
        '--set', 'http2=false',
        '--set', 'ssl_insecure=true',
        '--set', 'console_eventlog_verbosity=error',
        '--set', 'termlog_verbosity=error',
        '-s', addon_path,
    ]

    env = None
    if is_local:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        libs_path = os.path.join(project_root, "tools", "mitmproxy", "libs")
        
        env = os.environ.copy()
        
        current_pythonpath = env.get('PYTHONPATH', '')
        if current_pythonpath:
            env['PYTHONPATH'] = libs_path + os.pathsep + current_pythonpath
        else:
            env['PYTHONPATH'] = libs_path
        
        print('[WebProxy] 设置 PYTHONPATH 包含本地依赖库')

    try:
        _proxy_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
            env=env
        )

        time.sleep(1.5)

        if _proxy_process.poll() is not None:
            print('[WebProxy] mitmdump 进程启动后立即退出，退出码: ' + str(_proxy_process.returncode))
            _proxy_process = None
            return False

        source_type = "本地内置" if is_local else "系统安装"
        print('[WebProxy] 代理服务器已启动 ({source}, mitmproxy): http://{host}:{port}'.format(
            source=source_type,
            host=_proxy_host,
            port=str(port)
        ))
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
