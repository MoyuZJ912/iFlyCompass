#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
mitmproxy 内置工具 - 将 mitmproxy 及其所有依赖复制到 tools/mitmproxy 目录

使用方法：
  python tools/install_mitmproxy.py

此脚本会：
1. 从当前 Python 环境复制 mitmproxy 可执行文件到 tools/mitmproxy/
2. 复制所有必需的依赖库到 tools/mitmproxy/libs/
3. 创建启动包装器，确保使用本地依赖
"""

import os
import sys
import io
import shutil
import subprocess
from pathlib import Path

# 设置 stdout 为 UTF-8 编码（解决 Windows GBK 编码问题）
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"
MITMPROXY_DIR = TOOLS_DIR / "mitmproxy"
LIBS_DIR = MITMPROXY_DIR / "libs"

# mitmproxy 核心依赖（从 pip show mitmproxy 获取）
# 格式：(导入名称, 目录名称) - 两者可能不同
MITMPROXY_DEPS = [
    ("aioquic", "aioquic"),
    ("argon2_cffi", "argon2"),
    ("asgiref", "asgiref"),
    ("bcrypt", "bcrypt"),
    ("Brotli", None),  # brotli.py 是单文件模块
    ("certifi", "certifi"),
    ("cryptography", "cryptography"),
    ("flask", "flask"),  # mitmproxy 自带 web 接口需要
    ("h11", "h11"),
    ("h2", "h2"),
    ("hyperframe", "hyperframe"),
    ("kaitaistruct", None),  # kaitaistruct.py 单文件
    ("ldap3", "ldap3"),
    ("mitmproxy_rs", "mitmproxy_rs"),
    ("msgpack", "msgpack"),
    ("publicsuffix2", "publicsuffix2"),
    ("pydivert", "pydivert"),
    ("pyOpenSSL", "OpenSSL"),  # 特殊情况：导入名 OpenSSL
    ("pyparsing", "pyparsing"),
    ("pyperclip", "pyperclip"),
    ("ruamel.yaml", "ruamel.yaml"),
    ("sortedcontainers", "sortedcontainers"),
    ("tornado", "tornado"),
    ("urwid", "urwid"),
    ("wsproto", "wsproto"),
    ("zstandard", "zstandard"),
    # mitmproxy 本身
    ("mitmproxy", "mitmproxy"),
    ("mitmproxy.io", "mitmproxy_io"),
]

# 需要复制的可执行文件
EXECUTABLES = ["mitmdump.exe" if sys.platform == "win32" else "mitmdump"]


def get_site_packages():
    """获取 site-packages 路径"""
    import site
    sp = site.getsitepackages()
    # 返回包含实际包的路径（通常是最后一个）
    for p in reversed(sp):
        if os.path.isdir(p) and os.path.exists(os.path.join(p, "mitmproxy")):
            return Path(p)
    # 回退：使用标准路径
    return Path(sp[-1]) if sp else Path(sys.prefix) / "Lib" / "site-packages"


def find_package_dir(pkg_name, site_packages):
    """在 site-packages 中查找包的实际目录或文件"""
    # 尝试直接匹配
    candidate = site_packages / pkg_name
    if candidate.exists():
        return candidate
    
    # 尝试将连字符/点转换为下划线
    normalized = pkg_name.replace("-", "_").replace(".", "_")
    candidate = site_packages / normalized
    if candidate.exists():
        return candidate
    
    # 尝试其他常见变体
    variants = [
        pkg_name.lower(),
        pkg_name.replace("_", "-"),
        pkg_name.replace("-", "_"),
    ]
    for variant in variants:
        candidate = site_packages / variant
        if candidate.exists():
            return candidate
    
    return None


def copy_package(import_name, dir_name, src_dir, dst_dir):
    """复制单个包及其子包"""
    # 优先使用指定的目录名
    if dir_name:
        target_name = dir_name
    else:
        target_name = import_name
    
    # 查找源路径
    pkg_path = find_package_dir(target_name, src_dir)
    
    if not pkg_path:
        print(f"  [WARN] Package not found: {import_name} (tried: {target_name})")
        return False

    dst_path = dst_dir / target_name
    
    try:
        if pkg_path.is_file():
            # 单文件模块（如 .py 文件）
            shutil.copy2(pkg_path, dst_path)
            print(f"  [OK] Copied module: {target_name}")
        else:
            # 包目录
            if dst_path.exists():
                shutil.rmtree(dst_path)
            shutil.copytree(pkg_path, dst_path)
            print(f"  [OK] Copied package: {target_name}/")
        
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to copy {target_name}: {e}")
        return False


def copy_executable(exec_name, scripts_dir, dst_dir):
    """复制可执行文件"""
    src = scripts_dir / exec_name
    if not src.exists():
        print(f"  [ERROR] Executable not found: {exec_name}")
        return False
    
    dst = dst_dir / exec_name
    shutil.copy2(src, dst)
    print(f"  [OK] Copied: {exec_name}")
    return True


def create_launcher_windows(mitmproxy_dir):
    """创建 Windows 启动器 (.bat)"""
    bat_content = f"""@echo off
REM iFlyCompass Local mitmproxy Launcher
REM This launcher ensures using local mitmproxy and its dependencies

setlocal

set "PYTHONPATH={mitmproxy_dir.absolute()}\\libs;%PYTHONPATH%"

"{mitmproxy_dir.absolute()}\\mitmdump.exe" %*
endlocal
"""
    bat_path = mitmproxy_dir / "run_mitmdump.bat"
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    print("  [OK] Created launcher: run_mitmdump.bat")


def create_launcher_unix(mitmproxy_dir):
    """创建 Unix/macOS 启动器 (.sh)"""
    sh_content = f"""#!/bin/bash
# iFlyCompass Local mitmproxy Launcher
# This launcher ensures using local mitmproxy and its dependencies

export PYTHONPATH="{mitmproxy_dir.absolute()}/libs:$PYTHONPATH"

exec "{mitmproxy_dir.absolute()}/mitmdump" "$@"
"""
    sh_path = mitmproxy_dir / "run_mitmdump.sh"
    with open(sh_path, 'w', encoding='utf-8') as f:
        f.write(sh_content)
    os.chmod(sh_path, 0o755)
    print("  [OK] Created launcher: run_mitmdump.sh")


def main():
    print("=" * 60)
    print("iFlyCompass - mitmproxy Bundling Tool")
    print("=" * 60)
    print()

    # 1. 创建目录结构
    print("[DIR] Creating directory structure...")
    MITMPROXY_DIR.mkdir(parents=True, exist_ok=True)
    LIBS_DIR.mkdir(parents=True, exist_ok=True)
    print()

    # 2. 获取源路径
    site_packages = get_site_packages()
    python_dir = Path(sys.prefix)
    scripts_dir = python_dir / "Scripts" if sys.platform == "win32" else python_dir / "bin"

    print(f"[SOURCE] Paths:")
    print(f"   site-packages: {site_packages}")
    print(f"   Scripts:      {scripts_dir}")
    print()

    # 3. 复制依赖包
    print("[DEPS] Copying mitmproxy and its dependencies...")
    failed_deps = []
    success_count = 0
    
    for import_name, dir_name in MITMPROXY_DEPS:
        success = copy_package(import_name, dir_name, site_packages, LIBS_DIR)
        if success:
            success_count += 1
        else:
            failed_deps.append(import_name)

    print()
    print(f"[RESULT] Copied {success_count}/{len(MITMPROXY_DEPS)} packages")
    
    if failed_deps:
        print(f"[WARN] Failed packages (may be optional): {', '.join(failed_deps)}")
    print()

    # 4. 复制可执行文件
    print("[EXE] Copying executables...")
    for exe in EXECUTABLES:
        copy_executable(exe, scripts_dir, MITMPROXY_DIR)
    print()

    # 5. 创建启动器
    print("[LAUNCHER] Creating launchers...")
    if sys.platform == "win32":
        create_launcher_windows(MITMPROXY_DIR)
    else:
        create_launcher_unix(MITMPROXY_DIR)
    print()

    # 6. 创建 __init__.py 使 libs 成为 Python 包
    init_file = LIBS_DIR / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# mitmproxy dependencies\n")
        print("  [OK] Created libs/__init__.py")

    # 7. 创建版本信息文件
    version_file = MITMPROXY_DIR / "VERSION.txt"
    try:
        import mitmproxy
        version = mitmproxy.__version__
    except:
        version = "unknown"
    
    with open(version_file, 'w') as f:
        f.write(f"{version}\n")
    print(f"  [OK] Recorded mitmproxy version: {version}")

    print()
    print("=" * 60)
    print("[SUCCESS] Installation complete!")
    print()
    print(f"[LOCATION] mitmproxy path: {MITMPROXY_DIR.absolute()}")
    print(f"[LOCATION] Dependencies:    {LIBS_DIR.absolute()}")
    print()
    print("[NEXT STEPS]")
    print("  1. proxy_server.py will auto-detect and use local mitmproxy")
    print("  2. To run manually, use the launcher:")
    if sys.platform == "win32":
        print(f"     {MITMPROXY_DIR / 'run_mitmdump.bat'} --help")
    else:
        print(f"     {MITMPROXY_DIR / 'run_mitmdump.sh'} --help")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[ABORTED] Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Installation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
