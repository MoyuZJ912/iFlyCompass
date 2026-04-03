# iFlyCompass

## 项目简介

**版本：REL2.0.0**

iFlyCompass 是一个多功能的 Web 应用平台，采用模块化架构设计，提供了多种实用工具和功能，包括：

- **聊天室功能**：支持创建、加入、管理聊天室，实时消息通信
- **小说阅读器**：支持多种编码格式，章节自动解析，阅读进度保存
- **表情包管理**：表情商城、个人收藏、表情包合集管理
- **用户管理**：支持用户注册、登录、权限管理
- **Passkey 管理**：支持生成和管理注册邀请码

## 技术栈

- **前端**：Vue.js 2.x、Element UI、Socket.IO 客户端
- **后端**：Flask 3.x、Python 3.8+
- **数据库**：SQLAlchemy ORM + SQLite
- **实时通信**：Flask-SocketIO
- **认证**：Flask-Login
- **架构**：Flask Blueprint 模块化设计

## 架构特点

### 模块化设计

项目采用 Flask Blueprint 进行模块化设计，每个业务领域独立成模块：

- **models/** - 数据库模型层
- **utils/** - 工具函数层
- **modules/** - 业务模块层
  - **auth/** - 用户认证模块
  - **chat/** - 聊天室模块
  - **novel/** - 小说阅读器模块
  - **sticker/** - 表情包管理模块
  - **main/** - 主页面模块

### 单一职责原则

每个模块专注于单一业务领域，代码结构清晰，易于维护和扩展。

### 高内聚低耦合

模块之间通过清晰的接口进行通信，降低了代码的耦合度，提高了可测试性。

## 功能特点

### 聊天室功能

- 支持创建带密码和不带密码的聊天室
- 实时消息通信，支持多人聊天
- 显示在线用户列表
- 聊天消息历史记录（最近20条）
- 聊天室管理（编辑、删除）
- 表情包功能：支持添加、使用和管理表情包
  - 表情商城：浏览和添加公开表情包
  - 表情包管理：管理已添加的表情包
  - 支持单个表情和表情合集
  - 本地缓存表情包，无需网络连接

### 小说阅读器

- 支持多种编码格式（GBK、GB2312、UTF-16、UTF-8-BOM）
- 自动章节解析，支持多种章节格式
- 阅读进度保存，自动跳转到上次阅读位置
- 沉浸式阅读模式，支持点击翻页
- 作者信息显示，最新章节显示

### 用户系统

- 用户注册和登录
- 基于 Passkey 的注册邀请机制
- 权限管理（普通用户、管理员、超级管理员）
- 永久会话（除非被其他终端顶号）

### 其他功能

- 必应每日壁纸展示
- 每日诗词推荐
- 响应式设计，支持移动端

## 安装和运行

### 环境要求

- Python 3.8 或更高版本
- pip 包管理工具

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行项目

```bash
python app.py
```

项目将在 `http://127.0.0.1:5002` 上运行。

### 打包为 EXE

```bash
pyinstaller --onefile --name iFlyCompass app.py
```

## 项目结构

```
iFlyCompass/
├── app.py                    # 应用入口（43行）
├── config.py                 # 配置管理
├── extensions.py             # Flask 扩展初始化
├── models/                   # 数据库模型层
│   ├── __init__.py
│   ├── user.py              # User, Passkey 模型
│   ├── chat.py              # ChatRoom 模型
│   ├── sticker.py           # UserSticker, PackSticker 模型
│   └── novel.py             # NovelReadingProgress 模型
├── utils/                    # 工具函数层
│   ├── __init__.py
│   ├── common.py            # 通用工具函数
│   └── file.py              # 文件处理工具
├── modules/                  # 业务模块层
│   ├── auth/                # 用户认证模块
│   │   ├── __init__.py
│   │   ├── routes.py        # 认证相关路由
│   │   └── api.py           # 用户管理 API
│   ├── chat/                # 聊天室模块
│   │   ├── __init__.py
│   │   ├── routes.py        # 聊天室路由
│   │   ├── api.py           # 聊天室 API
│   │   └── websocket.py     # WebSocket 事件处理
│   ├── novel/               # 小说阅读器模块
│   │   ├── __init__.py
│   │   ├── routes.py        # 小说阅读器路由
│   │   ├── api.py           # 小说 API
│   │   └── parser.py        # 章节解析器
│   ├── sticker/             # 表情包管理模块
│   │   ├── __init__.py
│   │   ├── routes.py        # 表情包路由
│   │   └── api.py           # 表情包 API
│   └── main/                # 主页面模块
│       ├── __init__.py
│       └── routes.py        # 主页面路由
├── assets/                   # 静态资源
│   ├── css/                 # CSS 文件
│   ├── js/                  # JavaScript 文件
│   └── images/              # 图片文件
├── templates/                # HTML 模板
│   ├── chat.html            # 聊天室页面
│   ├── chat-simple.html     # 简化版聊天页面
│   ├── novel_reader.html    # 小说阅读器页面
│   ├── immersive_reader.html # 沉浸式阅读器页面
│   ├── index.html           # 首页
│   ├── login.html           # 登录页面
│   ├── register.html        # 注册页面
│   ├── board.html           # 控制面板页面
│   ├── user_management.html # 用户管理页面
│   ├── passkey_management.html # Passkey 管理页面
│   └── tools.html           # 工具页面
├── instance/                 # 数据库文件目录
│   ├── users.db             # 用户数据库
│   └── novels/              # 小说文件目录
├── stickers/                 # 表情包缓存目录
├── temp/                     # 临时文件目录
└── requirements.txt          # 依赖文件
```

## 首次使用

1. 启动应用后，访问 `http://127.0.0.1:5002`
2. 点击 "注册" 按钮，创建第一个用户（自动成为超级管理员）
3. 使用创建的账号登录
4. 进入 "Passkey 管理" 页面，生成邀请码
5. 其他用户可以使用邀请码注册

## 开发指南

详细的开发文档请参阅 [DEVELOPMENT.md](DEVELOPMENT.md)。

## 许可证

本项目采用 GNU GPL v3.0 许可证。
