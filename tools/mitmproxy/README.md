# mitmproxy 本地内置版本

本目录包含 iFlyCompass 网页代理功能所需的 **mitmproxy** 及其所有依赖库。

## 📁 目录结构

```
tools/mitmproxy/
├── mitmdump.exe          # mitmproxy 可执行文件（Windows）
├── run_mitmdump.bat      # Windows 启动器（自动设置 PYTHONPATH）
├── VERSION.txt           # 版本信息
└── libs/                 # 所有依赖库
    ├── mitmproxy/        # mitmproxy 主包
    ├── aioquic/          # QUIC/HTTP3 协议支持
    ├── cryptography/     # 加密库
    ├── OpenSSL/          # SSL/TLS 支持
    ├── flask/            # Web 界面
    └── ...               # 其他 25+ 个依赖包
```

## 🚀 安装与使用

### 首次安装

```bash
python tools/install_mitmproxy.py
```

此脚本会：
1. 从当前 Python 环境复制 mitmproxy 可执行文件
2. 复制所有必需的依赖（约 25 个包）到 `libs/` 目录
3. 创建启动器脚本

### 测试安装

```bash
python tools/test_mitmproxy.py
```

验证：
- ✅ mitmdump.exe 是否存在
- ✅ 依赖库是否完整
- ✅ mitmdump 是否可以正常运行

### 手动运行（可选）

```bash
# Windows
tools\mitmproxy\run_mitmdump.bat --help

# Linux/macOS
tools/mitmproxy/run_mitmdump.sh --help
```

## 🔧 工作原理

### 自动检测

[proxy_server.py](../../modules/proxy/proxy_server.py) 会自动按以下顺序查找 mitmproxy：

1. **本地内置版本**（优先）：`tools/mitmproxy/mitmdump.exe`
2. **系统安装版本**（回退）：Python Scripts 目录或 PATH

### PYTHONPATH 设置

当使用本地内置版本时，`proxy_server.py` 会自动设置 `PYTHONPATH`：

```python
env['PYTHONPATH'] = 'tools/mitmproxy/libs;' + 原始PYTHONPATH
```

这确保 mitmdump 使用项目自带的依赖，而不是系统安装的版本。

## 📦 包含的依赖

核心依赖（28个包）：

| 包名 | 用途 |
|------|------|
| mitmproxy | 主程序 |
| aioquic | QUIC/HTTP3 协议 |
| cryptography | TLS/SSL |
| OpenSSL | 底层加密 |
| h2, h11, hyperframe | HTTP/2 和 HTTP/1.1 |
| tornado | 异步框架 |
| flask | Web UI |
| ruamel.yaml | 配置文件解析 |
| certifi | CA 证书 |
| bcrypt, argon2 | 密码哈希 |
| wsproto | WebSocket |
| zstandard | 压缩 |
| ... | 其他辅助库 |

## 🔄 更新 mitmproxy

如果需要更新到新版本：

```bash
# 1. 升级系统 mitmproxy
pip install --upgrade mitmproxy

# 2. 重新运行安装脚本
python tools/install_mitmproxy.py

# 3. 测试
python tools/test_mitmproxy.py
```

## ⚠️ 注意事项

### 平台兼容性

- **Windows**: 已测试 ✓（使用 .exe 文件）
- **Linux**: 应该工作（需要重新运行 install 脚本）
- **macOS**: 应该工作（需要重新运行 install 脚本）

### Python 版本

需要与主应用程序相同的 Python 版本（当前为 Python 3.13）。

### Git 管理

默认情况下，`.gitignore` 会忽略 `tools/mitmproxy/` 目录。

**原因**：
- 文件较大（约 50-100MB）
- 不同平台可能需要不同的二进制文件
- 可以通过 `install_mitmproxy.py` 重建

如需提交到 Git，请编辑 `.gitignore` 删除相关行。

## 🐛 故障排除

### 问题：mitmdump 启动失败

**解决方案**：
```bash
# 检查依赖是否完整
python tools/test_mitmproxy.py

# 如果失败，重新安装
python tools/install_mitmproxy.py
```

### 问题：找不到模块

**原因**：PYTHONPATH 未正确设置

**解决方案**：检查 `proxy_server.py` 日志输出，确认看到：
```
[WebProxy] 设置 PYTHONPATH 包含本地依赖库
```

### 问题：SSL 错误

**原因**：OpenSSL 或 cryptography 版本不匹配

**解决方案**：
```bash
pip install --upgrade cryptography pyOpenSSL
python tools/install_mitmproxy.py
```

## 📊 版本信息

当前安装的版本：**mitmproxy 12.2.2**

查看完整版本信息：
```bash
tools\mitmproxy\run_mitmdump.bat --version
```

---

**最后更新**: 2026-05-06
**维护者**: iFlyCompass 开发团队
