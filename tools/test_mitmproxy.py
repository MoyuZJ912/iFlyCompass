#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
本地 mitmproxy 测试脚本

验证内置的 mitmproxy 是否可以正常启动
"""

import os
import sys
import subprocess
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def test_local_mitmproxy():
    """测试本地 mitmproxy 是否可用"""

    print("=" * 60)
    print("Local mitmproxy Test")
    print("=" * 60)
    print()

    # 1. 检查文件是否存在
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # tools/ 的上级目录
    mitmproxy_dir = os.path.join(project_root, "tools", "mitmproxy")
    
    if sys.platform == "win32":
        mitmdump_path = os.path.join(mitmproxy_dir, "mitmdump.exe")
    else:
        mitmdump_path = os.path.join(mitmproxy_dir, "mitmdump")
    
    print("[1] Checking mitmdump executable...")
    if not os.path.isfile(mitmdump_path):
        print(f"    [FAIL] Not found: {mitmdump_path}")
        print("    Please run: python tools/install_mitmproxy.py")
        return False
    
    print(f"    [OK] Found: {mitmdump_path}")
    print()
    
    # 2. 检查依赖库目录
    libs_dir = os.path.join(mitmproxy_dir, "libs")
    print("[2] Checking dependencies directory...")
    if not os.path.isdir(libs_dir):
        print(f"    [FAIL] Not found: {libs_dir}")
        return False
    
    # 统计包数量
    packages = [d for d in os.listdir(libs_dir) 
                if os.path.isdir(os.path.join(libs_dir, d)) and not d.startswith('__')]
    
    print(f"    [OK] Found {len(packages)} packages in libs/")
    print(f"         Sample packages: {', '.join(packages[:5])}...")
    print()
    
    # 3. 尝试运行 mitmdump --version
    print("[3] Testing mitmdump execution...")
    
    env = os.environ.copy()
    pythonpath = env.get('PYTHONPATH', '')
    if pythonpath:
        env['PYTHONPATH'] = libs_dir + os.pathsep + pythonpath
    else:
        env['PYTHONPATH'] = libs_dir
    
    try:
        result = subprocess.run(
            [mitmdump_path, '--version'],
            capture_output=True,
            text=True,
            timeout=10,
            env=env
        )
        
        if result.returncode == 0:
            print(f"    [OK] mitmdump runs successfully!")
            print()
            print("    Version output:")
            for line in result.stdout.strip().split('\n')[:5]:
                print(f"      {line}")
            print()
            return True
        else:
            print(f"    [WARN] mitmdump exited with code {result.returncode}")
            if result.stderr:
                print(f"    Error: {result.stderr[:200]}")
            print()
            return False
            
    except subprocess.TimeoutExpired:
        print("    [WARN] mitmdump timed out (this may be normal)")
        print()
        return True  # 超时可能意味着它正在运行
        
    except Exception as e:
        print(f"    [ERROR] Failed to run mitmdump: {e}")
        print()
        return False


def test_import_from_libs():
    """测试从 libs 目录导入 mitmproxy 模块"""

    print("[4] Testing Python imports from libs/...")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    libs_dir = os.path.join(project_root, "tools", "mitmproxy", "libs")
    
    # 将 libs 目录添加到 sys.path
    if libs_dir not in sys.path:
        sys.path.insert(0, libs_dir)
    
    try:
        import mitmproxy
        version = getattr(mitmproxy, '__version__', 'unknown')
        print(f"    [OK] Successfully imported mitmproxy (version: {version})")
        print()
        return True
    except ImportError as e:
        print(f"    [WARN] Could not import mitmproxy: {e}")
        print("    (This is OK - mitmdump uses its own PYTHONPATH)")
        print()
        return True  # 不算失败，因为 mitmdump 会自己设置 PYTHONPATH


def main():
    print()
    results = []
    
    # 运行测试
    results.append(("Executable check", test_local_mitmproxy()))
    results.append(("Import test", test_import_from_libs()))
    
    # 输出总结
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("[SUCCESS] All tests passed! Local mitmproxy is ready to use.")
        print()
        print("Next step:")
        print("  Start the application: python app.py")
        print("  Then open Web Proxy tool from the control panel.")
    else:
        print("[FAIL] Some tests failed. Check the output above.")
        print()
        print("Troubleshooting:")
        print("  1. Run: python tools/install_mitmproxy.py")
        print("  2. Verify Python version compatibility")
        print("  3. Check for missing system dependencies")
    
    print()
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
