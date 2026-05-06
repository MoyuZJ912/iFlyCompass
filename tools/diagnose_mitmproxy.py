#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
mitmproxy 生产环境诊断工具

用于诊断生产环境中 mitmdump 启动失败的问题

使用方法：
  python tools/diagnose_mitmproxy.py
"""

import os
import sys
import subprocess
import platform
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def print_section(title):
    """打印分节标题"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def check_python_env():
    """检查 Python 环境"""
    print_section("1. Python 环境")
    
    print(f"Python 版本: {sys.version}")
    print(f"Python 路径: {sys.executable}")
    print(f"Python 目录: {os.path.dirname(sys.executable)}")
    print(f"平台: {platform.system()} {platform.release()}")
    print(f"架构: {platform.machine()}")
    
    # 检查虚拟环境
    if hasattr(sys, 'prefix'):
        print(f"Python prefix: {sys.prefix}")
        if hasattr(sys, 'base_prefix'):
            print(f"Base prefix: {sys.base_prefix}")
            if sys.prefix != sys.base_prefix:
                print("✓ 检测到虚拟环境")
            else:
                print("✓ 使用系统 Python")


def check_mitmproxy_installation():
    """检查 mitmproxy 安装情况"""
    print_section("2. mitmproxy 安装检查")
    
    # 检查系统安装
    try:
        import mitmproxy
        version = getattr(mitmproxy, '__version__', None)
        if not version:
            # 尝试从 mitmproxy.main 获取版本
            try:
                from mitmproxy import main
                version = getattr(main, 'VERSION', 'unknown')
            except:
                version = 'unknown'
        
        print(f"✓ 系统安装 mitmproxy: {version}")
        print(f"  位置: {mitmproxy.__file__}")
    except ImportError:
        print("✗ 系统未安装 mitmproxy")
    
    # 检查本地内置版本
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    mitmproxy_dir = os.path.join(project_root, "tools", "mitmproxy")
    
    print(f"\n本地内置版本目录: {mitmproxy_dir}")
    
    if sys.platform == "win32":
        mitmdump_exe = os.path.join(mitmproxy_dir, "mitmdump.exe")
    else:
        mitmdump_exe = os.path.join(mitmproxy_dir, "mitmdump")
    
    if os.path.isfile(mitmdump_exe):
        print(f"✓ 找到本地 mitmdump: {mitmdump_exe}")
        print(f"  文件大小: {os.path.getsize(mitmdump_exe)} bytes")
    else:
        print(f"✗ 未找到本地 mitmdump: {mitmdump_exe}")
    
    # 检查依赖库
    libs_dir = os.path.join(mitmproxy_dir, "libs")
    if os.path.isdir(libs_dir):
        packages = [d for d in os.listdir(libs_dir) 
                    if os.path.isdir(os.path.join(libs_dir, d)) and not d.startswith('__')]
        print(f"✓ 本地依赖库目录存在: {libs_dir}")
        print(f"  包含 {len(packages)} 个包")
        
        # 检查关键依赖
        critical_deps = ["mitmproxy", "cryptography", "OpenSSL", "tornado", "flask"]
        missing = []
        for dep in critical_deps:
            if os.path.isdir(os.path.join(libs_dir, dep)):
                print(f"  ✓ {dep}")
            else:
                print(f"  ✗ {dep} (缺失)")
                missing.append(dep)
        
        if missing:
            print(f"\n⚠️  缺少关键依赖: {', '.join(missing)}")
            print("   请运行: python tools/install_mitmproxy.py")
    else:
        print(f"✗ 本地依赖库目录不存在: {libs_dir}")


def check_mitmdump_execution():
    """检查 mitmdump 可执行性"""
    print_section("3. mitmdump 执行测试")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    mitmproxy_dir = os.path.join(project_root, "tools", "mitmproxy")
    
    if sys.platform == "win32":
        mitmdump_exe = os.path.join(mitmproxy_dir, "mitmdump.exe")
    else:
        mitmdump_exe = os.path.join(mitmproxy_dir, "mitmdump")
    
    if not os.path.isfile(mitmdump_exe):
        print("✗ mitmdump 不存在，跳过执行测试")
        return
    
    # 测试 1: 直接运行 --version
    print("\n测试 1: 运行 mitmdump --version")
    try:
        result = subprocess.run(
            [mitmdump_exe, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✓ 执行成功")
            print(f"输出:\n{result.stdout[:500]}")
        else:
            print(f"✗ 执行失败，退出码: {result.returncode}")
            if result.stderr:
                print(f"错误输出:\n{result.stderr[:500]}")
    except subprocess.TimeoutExpired:
        print("⚠️  执行超时")
    except Exception as e:
        print(f"✗ 执行异常: {e}")
    
    # 测试 2: 设置 PYTHONPATH 后运行
    print("\n测试 2: 设置 PYTHONPATH 后运行")
    libs_dir = os.path.join(mitmproxy_dir, "libs")
    
    env = os.environ.copy()
    current_pythonpath = env.get('PYTHONPATH', '')
    if current_pythonpath:
        env['PYTHONPATH'] = libs_dir + os.pathsep + current_pythonpath
    else:
        env['PYTHONPATH'] = libs_dir
    
    print(f"PYTHONPATH: {env['PYTHONPATH']}")
    
    try:
        result = subprocess.run(
            [mitmdump_exe, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            env=env
        )
        
        if result.returncode == 0:
            print("✓ 执行成功")
            print(f"输出:\n{result.stdout[:500]}")
        else:
            print(f"✗ 执行失败，退出码: {result.returncode}")
            if result.stderr:
                print(f"错误输出:\n{result.stderr[:500]}")
    except subprocess.TimeoutExpired:
        print("⚠️  执行超时")
    except Exception as e:
        print(f"✗ 执行异常: {e}")


def check_dependencies():
    """检查关键依赖包"""
    print_section("4. 关键依赖包检查")
    
    critical_packages = [
        "mitmproxy",
        "cryptography",
        "OpenSSL",
        "tornado",
        "flask",
        "aioquic",
        "h2",
        "h11",
        "certifi",
        "urllib3",
    ]
    
    for pkg in critical_packages:
        try:
            module = __import__(pkg)
            version = getattr(module, '__version__', 'unknown')
            location = getattr(module, '__file__', 'unknown')
            print(f"✓ {pkg:20s} {version:15s} {location}")
        except ImportError:
            print(f"✗ {pkg:20s} 未安装")


def check_network_ports():
    """检查网络端口占用"""
    print_section("5. 网络端口检查")
    
    proxy_port = 5003
    
    import socket
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    
    try:
        result = sock.connect_ex(('127.0.0.1', proxy_port))
        if result == 0:
            print(f"⚠️  端口 {proxy_port} 已被占用")
            print("   可能已有 mitmdump 进程在运行")
        else:
            print(f"✓ 端口 {proxy_port} 可用")
    except Exception as e:
        print(f"✗ 端口检查失败: {e}")
    finally:
        sock.close()


def check_ssl_certificates():
    """检查 SSL 证书"""
    print_section("6. SSL 证书检查")
    
    # mitmproxy 证书通常在用户目录
    home = os.path.expanduser("~")
    mitmproxy_dir = os.path.join(home, ".mitmproxy")
    
    if os.path.isdir(mitmproxy_dir):
        print(f"✓ mitmproxy 配置目录存在: {mitmproxy_dir}")
        
        cert_files = [
            "mitmproxy-ca.pem",
            "mitmproxy-ca-cert.pem",
            "mitmproxy-ca-cert.cer",
            "mitmproxy-ca-cert.p12",
        ]
        
        for cert in cert_files:
            cert_path = os.path.join(mitmproxy_dir, cert)
            if os.path.isfile(cert_path):
                print(f"  ✓ {cert}")
            else:
                print(f"  ✗ {cert} (缺失)")
    else:
        print(f"⚠️  mitmproxy 配置目录不存在: {mitmproxy_dir}")
        print("   首次运行 mitmdump 会自动创建")


def check_file_permissions():
    """检查文件权限（Unix/Linux/macOS）"""
    if sys.platform == "win32":
        return
    
    print_section("7. 文件权限检查")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    mitmproxy_dir = os.path.join(project_root, "tools", "mitmproxy")
    mitmdump_exe = os.path.join(mitmproxy_dir, "mitmdump")
    
    if os.path.isfile(mitmdump_exe):
        import stat
        mode = os.stat(mitmdump_exe).st_mode
        if mode & stat.S_IXUSR:
            print(f"✓ mitmdump 有执行权限")
        else:
            print(f"✗ mitmdump 没有执行权限")
            print(f"   运行: chmod +x {mitmdump_exe}")


def generate_report():
    """生成诊断报告"""
    print("\n" + "=" * 60)
    print(" mitmproxy 生产环境诊断工具")
    print("=" * 60)
    
    check_python_env()
    check_mitmproxy_installation()
    check_dependencies()
    check_mitmdump_execution()
    check_network_ports()
    check_ssl_certificates()
    check_file_permissions()
    
    print_section("诊断完成")
    print("\n如果发现问题，请按以下步骤排查：")
    print("1. 缺少依赖: python tools/install_mitmproxy.py")
    print("2. 端口占用: 检查是否有其他 mitmdump 进程")
    print("3. 权限问题: chmod +x tools/mitmproxy/mitmdump (Unix/Linux/macOS)")
    print("4. 查看错误日志: logs/mitmdump_error.log")
    print("5. 手动测试: tools/mitmproxy/run_mitmdump.bat --version")
    print()


if __name__ == "__main__":
    try:
        generate_report()
    except KeyboardInterrupt:
        print("\n\n诊断已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n诊断失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
