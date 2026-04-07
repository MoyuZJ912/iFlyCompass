# iFlyCompass 开发文档

## 版本更新

### EVA2.1.1

**随身听兼容性修复**

- **修复 APlayer API 错误**：
  - 将 `this.aplayer.skip(index)` 改为 `this.aplayer.list.switch(index) + this.aplayer.play()`
  - APlayer 正确的方法是使用 `list.switch(index)` 切换歌曲

- **添加旧版 WebView 兼容性处理**：
  - 检测 `localStorage` 是否存在，不存在则创建 mock 对象
  - 检测 `localStorage` 是否可用，失败则替换为 mock
  - 提供 `getItem`, `setItem`, `removeItem`, `clear` 方法
  - 解决旧版 WebView 中 `Cannot read property 'getItem' of null` 错误

- **播放器操作容错处理**：
  - 添加空值检查：`this.aplayer.list` 和 `this.aplayer.list.audios`
  - 添加 try-catch 保护，播放器操作失败时自动尝试重新创建
  - 双重保护机制，即使初始化失败也会尝试再次创建

- **错误提示优化**：
  - 播放失败时显示具体原因
  - `无法获取播放地址: 歌曲暂无播放地址` / `API返回错误码: xxx`
  - `缓存音乐失败: xxx`（后端返回的具体错误信息）
  - `播放失败: xxx`（JavaScript 异常的消息）

- **添加详尽的日志记录**：
  - 前端日志：`[NCM]` 前缀的各步骤日志
  - 后端日志：`[NCM API]` / `[MusicCache]` 前缀的详细日志

### EVA2.1.0

**性能优化 + 随身听功能**

- **小说缓存优化**：
  - 新增 `utils/novel_cache.py` 小说缓存服务
  - 启动时预扫描所有小说，缓存书名、作者、最新章节
  - API 响应从数秒优化到毫秒级
  - 支持手动刷新缓存 `/api/novels/refresh-cache`

- **随身听功能**：
  - 新增 `modules/ncm/` 随身听模块
  - 网易云音乐播放器，支持搜索、推荐歌单、热门搜索
  - 内网缓存播放：音乐文件先缓存到本地 `temp/music/`
  - APlayer 播放器本地化部署，无需外网 CDN
  - 与聊天室、小说阅读器保持一致的设计风格

- **新增文件**：
  - `utils/novel_cache.py` - 小说缓存服务
  - `utils/music_cache.py` - 音乐缓存服务
  - `utils/ncm_api.py` - 网易云音乐 API 封装
  - `modules/ncm/__init__.py` - 随身听模块定义
  - `modules/ncm/routes.py` - 播放器页面路由
  - `modules/ncm/api.py` - NCM API 接口
  - `templates/ncm_player.html` - 播放器前端页面
  - `assets/css/aplayer.min.css` - APlayer 样式
  - `assets/js/aplayer.min.js` - APlayer 脚本

- **新增 API**：
  - `GET /api/ncm/search` - 搜索歌曲
  - `GET /api/ncm/song/url` - 获取歌曲播放地址
  - `GET /api/ncm/personalized` - 获取推荐歌单
  - `GET /api/ncm/hot-search` - 获取热搜列表
  - `GET /api/ncm/playlist/detail` - 获取歌单详情
  - `POST /api/ncm/cache-music` - 缓存音乐到本地
  - `GET /music/<filename>` - 提供缓存的音乐文件

### REL2.0.2

**用户管理系统优化**

- **用户管理简化**：
  - 取消编辑用户对话框，管理员开关直接在表格中切换
  - 用户名不可修改，仅作为登录标识
  - 密码修改通过"重置密码"按钮单独操作

- **昵称功能**：
  - 新增 `nickname` 字段，用户可设置昵称
  - 所有页面优先显示昵称，无昵称时显示用户名
  - 用户可在"个人设置"中修改自己的昵称

- **超级管理员密码修改**：
  - 超级管理员可在"个人设置"中修改自己的密码

- **下拉菜单优化**：
  - 所有页面下拉菜单统一风格
  - 显示大字昵称 + 小字用户名
  - 添加"个人设置"入口

- **Bug修复**：
  - 修复控制台欢迎页面用户名不显示的问题
  - 数据库自动迁移：启动时检查并添加 `nickname` 字段

### REL2.0.1

**小说阅读器增强**

- **智能章节解析算法 V3.1**：
  - 采用锚点学习 + 统计验证的五阶段检测算法
  - Phase 1 - 发现：使用锚点规则和宽松规则发现章节候选
  - Phase 2 - 模式学习：从锚点学习标题长度、前缀模式、间距等特征
  - Phase 3 - 模式扩展：用学习到的模式搜索遗漏的章节
  - Phase 4 - 统计验证：两阶段间距验证，过滤误检
  - Phase 5 - 层级推断：识别卷/章/节层级
  - 支持中英文多种章节格式（第一章、Chapter 1、1. 等）
  - 章节标题前空行强制校验，避免正文中关键词误识别
  - 新增 `utils/chapter_parser.py` 作为独立章节解析库

- **沉浸式阅读器主题系统**：
  - 日间模式 5 种主题：牛奶白、卷轴黄、小草绿、基佬紫、云雾蓝
  - 夜间模式 2 种主题：星空黑、玄素灰
  - 一键切换日间/夜间模式
  - 设置面板风格与阅读器主题同步

- **翻页动画系统重构**：
  - 双层页面结构，动画过程中可同时看到两页
  - 滑动动画：当前页向左滑出，下一页从右边滑入
  - 滚动动画：当前页向上滚出，下一页从下边滚入
  - 淡入淡出动画：页面渐隐渐现
  - 无动画选项：直接切换
  - 所有设置自动保存到 localStorage

### REL2.0.0

**重大架构重构**

- **模块化重构**：将 1680 行的 app.py 拆分为清晰的模块化结构
  - 创建 models/ 目录，按业务领域组织数据库模型
  - 创建 utils/ 目录，统一管理工具函数
  - 创建 modules/ 目录，按业务领域组织功能模块
  - app.py 从 1680 行减少到 43 行（减少 97.4%）

- **架构改进**：
  - 采用 Flask Blueprint 进行模块化设计
  - 遵循单一职责原则，每个模块专注于单一业务领域
  - 提高代码的可维护性、可测试性和可扩展性
  - 改善多人协作，减少合并冲突

- **新增模块**：
  - **models/** - 数据库模型层
    - user.py：User, Passkey 模型
    - chat.py：ChatRoom 模型
    - sticker.py：UserSticker, PackSticker 模型
    - novel.py：NovelReadingProgress 模型
  - **utils/** - 工具函数层
    - common.py：通用工具函数（壁纸、诗词、Passkey 生成等）
    - file.py：文件处理工具（编码检测、文件读取、图片下载等）
  - **modules/** - 业务模块层
    - auth/：用户认证模块（登录、注册、用户管理、Passkey 管理）
    - chat/：聊天室模块（聊天室管理、WebSocket 事件处理）
    - novel/：小说阅读器模块（小说列表、章节解析、阅读进度）
    - sticker/：表情包管理模块（表情商城、个人收藏、表情包合集）
    - main/：主页面模块（首页、控制面板、工具页面）

- **代码质量提升**：
  - 配置集中管理（config.py）
  - 扩展统一初始化（extensions.py）
  - 清晰的模块边界和职责划分
  - 更好的代码复用性

### REL1.3.4_fix1

- **修复**：沉浸式阅读器章节切换bug
  - 修复章节结尾快速点击导致跳过多章的问题
  - 添加章节加载锁，在章节切换过程中屏蔽点击换页功能

### REL1.3.4

- **新增**：沉浸式阅读器功能
  - 在小说阅读器章节导航右侧添加全屏图标按钮
  - 创建独立的沉浸式阅读器页面
  - 点击屏幕左侧翻到上一页，点击右侧翻到下一页
  - 点击屏幕中间弹出/收回顶部和底部菜单栏
  - 一章读完后自动进入下一章
  - 根据浏览器窗口实际宽高动态计算文字显示范围和分页
  - 支持高DPI设备，宁可少显示一行也不让文字溢出屏幕
  - 每章第一页顶部显示章节名称标题
  - 左下角显示当前时间、书名、章节名称、页数信息
  - 后台预加载后两章节，提升阅读体验
- **更新**：依赖库版本
  - Flask 2.0.1 → 3.1.2
  - Flask-SQLAlchemy 2.5.1 → 3.1.1
  - Flask-Login 0.5.0 → 0.6.3
  - Flask-SocketIO 5.1.1 → 5.6.1
  - requests 2.26.0 → 2.32.5
  - Werkzeug 2.0.1 → 3.1.4
  - python-socketio 5.5.0 → 5.16.1
  - python-engineio 4.3.0 → 4.13.1
  - chardet 5.2.0 → 7.4.0.post2
  - 新增 flask-cors 6.0.2

## 1. 项目架构

### 1.1 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                        Flask Application                     │
│                         (app.py - 43行)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
                ▼             ▼             ▼
        ┌───────────┐  ┌───────────┐  ┌───────────┐
        │  Config   │  │Extensions │  │  Models   │
        │ (config.py)│  │(extensions)│  │ (models/) │
        └───────────┘  └───────────┘  └───────────┘
                                           │
                              ┌────────────┼────────────┐
                              │            │            │
                              ▼            ▼            ▼
                        ┌─────────┐  ┌─────────┐  ┌─────────┐
                        │  User   │  │  Chat   │  │ Sticker │
                        │ Passkey │  │  Room   │  │  Models │
                        └─────────┘  └─────────┘  └─────────┘
                
                ┌─────────────────────────────────────┐
                │         Business Modules            │
                │           (modules/)                │
                └─────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  Auth Module  │    │  Chat Module  │    │ Novel Module  │
│   (auth/)     │    │   (chat/)     │    │  (novel/)     │
│               │    │               │    │               │
│ - routes.py   │    │ - routes.py   │    │ - routes.py   │
│ - api.py      │    │ - api.py      │    │ - api.py      │
│               │    │ - websocket.py│    │ - parser.py   │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                    ┌───────────────┐
                    │Sticker Module │
                    │  (sticker/)   │
                    │               │
                    │ - routes.py   │
                    │ - api.py      │
                    └───────────────┘
```

### 1.2 前端架构

- **框架**：Vue.js 2.x
- **UI 库**：Element UI
- **通信**：Socket.IO 客户端
- **构建**：原生 HTML/CSS/JavaScript，无构建工具

### 1.3 后端架构

#### 1.3.1 核心组件

- **app.py**：应用入口，负责创建和配置 Flask 应用
- **config.py**：配置管理，集中管理所有配置项
- **extensions.py**：扩展初始化，统一初始化 Flask 扩展

#### 1.3.2 模块化设计

采用 Flask Blueprint 进行模块化设计，每个模块独立管理路由和业务逻辑：

- **auth 模块**：用户认证和管理
  - routes.py：登录、注册、用户管理页面
  - api.py：用户和 Passkey 管理 API

- **chat 模块**：聊天室功能
  - routes.py：聊天室页面路由
  - api.py：聊天室管理 API
  - websocket.py：WebSocket 事件处理

- **novel 模块**：小说阅读器
  - routes.py：小说阅读器页面路由
  - api.py：小说和章节 API
  - parser.py：章节解析器（支持高级/简单两种模式）

- **sticker 模块**：表情包管理
  - routes.py：表情包文件服务
  - api.py：表情包管理 API

- **main 模块**：主页面
  - routes.py：首页、控制面板、工具页面

#### 1.3.3 数据模型层

独立的数据模型层，按业务领域组织：

- **user.py**：User, Passkey
- **chat.py**：ChatRoom
- **sticker.py**：UserSticker, PackSticker
- **novel.py**：NovelReadingProgress

#### 1.3.4 工具函数层

统一的工具函数层，提供通用功能：

- **common.py**：
  - get_bing_wallpaper()：获取必应壁纸
  - get_poetry()：获取今日诗词
  - generate_passkey()：生成 Passkey
  - get_utc_plus_8_time()：获取 UTC+8 时间

- **file.py**：
  - detect_file_encoding()：检测文件编码
  - read_novel_content()：读取小说内容
  - download_sticker_image()：下载表情包图片

- **chapter_parser.py**：
  - parse_chapters_advanced()：高级章节解析，返回章节列表
  - detect_chapters()：从文件检测章节位置
  - detect_chapters_from_lines()：从行列表检测章节
  - V3.1 锚点学习 + 统计验证算法

### 1.4 架构优势

#### 1.4.1 可维护性

- 每个模块职责单一，代码量适中（200-400行）
- 清晰的模块边界，易于定位和修改代码
- 配置集中管理，便于调整

#### 1.4.2 可测试性

- 模块独立，便于编写单元测试
- 依赖注入，便于模拟和测试
- 清晰的接口定义

#### 1.4.3 可扩展性

- 新增功能只需添加新模块
- 模块之间松耦合，便于替换和升级
- 支持水平扩展

#### 1.4.4 团队协作

- 不同开发者可以同时修改不同模块
- 减少合并冲突
- 清晰的代码结构，便于新成员上手

## 2. 数据库设计

### 2.1 用户表 (User)

| 字段名              | 类型          | 描述             |
| ------------------- | ------------- | ---------------- |
| id                  | Integer       | 用户 ID，主键     |
| username            | String(50)    | 用户名，唯一      |
| password_hash       | String(128)   | 密码哈希值        |
| is_super_admin      | Boolean       | 是否为超级管理员  |
| is_admin            | Boolean       | 是否为管理员      |
| passkey_used        | String(6)     | 注册时使用的 Passkey |
| created_at          | DateTime      | 创建时间          |

### 2.2 Passkey 表 (Passkey)

| 字段名            | 类型        | 描述                |
| ----------------- | ----------- | ------------------- |
| id                | Integer     | Passkey ID，主键     |
| key               | String(6)   | Passkey 值，唯一     |
| duration_days     | Integer     | 有效期（天数），None 表示无限 |
| max_uses          | Integer     | 最大使用次数，None 表示无限  |
| current_uses      | Integer     | 当前使用次数         |
| is_active         | Boolean     | 是否激活             |
| expires_at        | DateTime    | 过期时间             |
| created_at        | DateTime    | 创建时间             |

### 2.3 聊天室表 (ChatRoom)

| 字段名         | 类型          | 描述                  |
| -------------- | ------------- | --------------------- |
| id             | Integer       | 聊天室 ID，主键        |
| name           | String(50)    | 聊天室名称，唯一       |
| password       | String(128)   | 密码哈希值，None 表示无密码 |
| created_by     | Integer       | 创建者 ID，外键关联 User.id |
| created_at     | DateTime      | 创建时间              |
| is_active      | Boolean       | 是否激活              |

### 2.4 用户表情包表 (UserSticker)

| 字段名           | 类型          | 描述                       |
| ---------------- | ------------- | -------------------------- |
| id               | Integer       | 表情包 ID，主键             |
| user_id          | Integer       | 用户 ID，外键关联 User.id   |
| sticker_code     | String(20)    | 表情码                     |
| sticker_type     | String(20)    | 表情类型 ('single' 或 'pack') |
| sticker_name     | String(100)   | 表情名称                   |
| description      | String(255)   | 表情描述                   |
| local_path       | String(255)   | 本地缓存路径               |
| created_at       | DateTime      | 创建时间                   |

### 2.5 表情包合集中的表情表 (PackSticker)

| 字段名           | 类型          | 描述                 |
| ---------------- | ------------- | -------------------- |
| id               | Integer       | 表情 ID，主键         |
| user_id          | Integer       | 用户 ID，外键关联 User.id |
| pack_code        | String(20)    | 所属表情包合集码      |
| sticker_code     | String(50)    | 表情码               |
| sticker_name     | String(100)   | 表情名称             |
| description      | String(255)   | 表情描述             |
| local_path       | String(255)   | 本地缓存路径         |
| created_at       | DateTime      | 创建时间             |

### 2.6 小说阅读进度表 (NovelReadingProgress)

| 字段名                  | 类型          | 描述                 |
| ----------------------- | ------------- | -------------------- |
| id                      | Integer       | 进度 ID，主键         |
| user_id                 | Integer       | 用户 ID，外键关联 User.id |
| novel_filename          | String(255)   | 小说文件名           |
| last_chapter_index      | Integer       | 最后阅读的章节索引    |
| last_read_at            | DateTime      | 最后阅读时间         |

## 3. API 接口

### 3.1 用户认证相关

#### 3.1.1 注册

- **URL**：`/register`
- **方法**：POST
- **参数**：
  - username: 用户名
  - password: 密码
  - confirm_password: 确认密码
  - passkey: 邀请码（可选，首个用户不需要）
- **返回**：重定向到登录页面

#### 3.1.2 登录

- **URL**：`/login`
- **方法**：POST
- **参数**：
  - username: 用户名
  - password: 密码
- **返回**：重定向到控制面板

#### 3.1.3 退出登录

- **URL**：`/logout`
- **方法**：GET
- **返回**：重定向到首页

### 3.2 用户管理 API

#### 3.2.1 获取用户列表

- **URL**：`/api/users`
- **方法**：GET
- **权限**：管理员或超级管理员
- **返回**：用户列表 JSON

#### 3.2.2 创建用户

- **URL**：`/api/users`
- **方法**：POST
- **权限**：管理员或超级管理员
- **参数**：
  - username: 用户名
  - password: 密码
  - is_admin: 是否为管理员（仅超级管理员可设置）
- **返回**：新用户信息 JSON

#### 3.2.3 更新用户

- **URL**：`/api/users`
- **方法**：PUT
- **权限**：管理员或超级管理员
- **参数**：
  - id: 用户 ID
  - password: 密码（可选）
  - is_admin: 是否为管理员（仅超级管理员可设置）
- **返回**：更新后的用户信息 JSON

#### 3.2.4 删除用户

- **URL**：`/api/users`
- **方法**：DELETE
- **权限**：管理员或超级管理员
- **参数**：
  - id: 用户 ID
- **返回**：成功/失败信息 JSON

### 3.3 Passkey 管理 API

#### 3.3.1 获取 Passkey 列表

- **URL**：`/api/passkeys`
- **方法**：GET
- **权限**：超级管理员
- **返回**：Passkey 列表 JSON

#### 3.3.2 创建 Passkey

- **URL**：`/api/passkeys`
- **方法**：POST
- **权限**：超级管理员
- **参数**：
  - duration_days: 有效期（天数，可选）
  - max_uses: 最大使用次数（可选）
- **返回**：新 Passkey 信息 JSON

#### 3.3.3 删除 Passkey

- **URL**：`/api/passkeys`
- **方法**：DELETE
- **权限**：超级管理员
- **参数**：
  - id: Passkey ID
- **返回**：成功/失败信息 JSON

### 3.4 聊天室相关 API

#### 3.4.1 获取聊天室列表

- **URL**：`/api/chatrooms`
- **方法**：GET
- **权限**：登录用户
- **返回**：聊天室列表 JSON

#### 3.4.2 创建聊天室

- **URL**：`/api/chatrooms`
- **方法**：POST
- **权限**：登录用户
- **参数**：
  - name: 聊天室名称
  - password: 密码（可选）
- **返回**：新聊天室信息 JSON

#### 3.4.3 编辑聊天室

- **URL**：`/api/chatrooms`
- **方法**：PUT
- **权限**：聊天室创建者或管理员
- **参数**：
  - id: 聊天室 ID
  - name: 聊天室名称
  - password: 密码（可选，空字符串表示清空密码）
- **返回**：更新后的聊天室信息 JSON

#### 3.4.4 删除聊天室

- **URL**：`/api/chatrooms/{room_id}`
- **方法**：DELETE
- **权限**：聊天室创建者或管理员
- **返回**：成功/失败信息 JSON

#### 3.4.5 加入聊天室

- **URL**：`/api/chatroom/join`
- **方法**：POST
- **权限**：登录用户
- **参数**：
  - room_id: 聊天室 ID
  - password: 密码（如果需要）
- **返回**：成功/失败信息 JSON

### 3.5 小说阅读器相关 API

#### 3.5.1 获取小说列表

- **URL**：`/api/novels`
- **方法**：GET
- **权限**：登录用户
- **返回**：小说列表 JSON

#### 3.5.2 获取章节列表

- **URL**：`/api/novels/{novel_name}/chapters`
- **方法**：GET
- **权限**：登录用户
- **返回**：章节列表 JSON

#### 3.5.3 获取章节内容

- **URL**：`/api/novels/{novel_name}/chapters/{chapter_index}`
- **方法**：GET
- **权限**：登录用户
- **返回**：章节内容 JSON

#### 3.5.4 保存阅读进度

- **URL**：`/api/novels/{novel_name}/progress`
- **方法**：POST
- **权限**：登录用户
- **参数**：
  - chapter_index: 章节索引
- **返回**：成功/失败信息 JSON

#### 3.5.5 获取阅读进度

- **URL**：`/api/novels/{novel_name}/progress`
- **方法**：GET
- **权限**：登录用户
- **返回**：阅读进度 JSON

### 3.6 表情包相关 API

#### 3.6.1 获取表情商城列表

- **URL**：`/api/stickers/hub`
- **方法**：GET
- **权限**：登录用户
- **参数**：
  - type: 表情类型 ('single' 或 'pack')
  - page: 页码（可选）
- **返回**：表情列表 JSON

#### 3.6.2 获取我的表情包

- **URL**：`/api/stickers/mine`
- **方法**：GET
- **权限**：登录用户
- **参数**：
  - type: 表情类型 ('single' 或 'pack')
- **返回**：我的表情包列表 JSON

#### 3.6.3 添加表情包

- **URL**：`/api/stickers/add`
- **方法**：POST
- **权限**：登录用户
- **参数**：
  - code: 表情码
  - type: 表情类型 ('single' 或 'pack')
- **返回**：成功/失败信息 JSON

#### 3.6.4 移除表情包

- **URL**：`/api/stickers/remove`
- **方法**：POST
- **权限**：登录用户
- **参数**：
  - id: 表情包 ID
- **返回**：成功/失败信息 JSON

#### 3.6.5 获取表情包分类

- **URL**：`/api/stickers/categories`
- **方法**：GET
- **权限**：登录用户
- **返回**：表情包分类列表 JSON

#### 3.6.6 获取表情包合集中的表情

- **URL**：`/api/stickers/pack/{code}`
- **方法**：GET
- **权限**：登录用户
- **参数**：
  - code: 表情包合集码
- **返回**：表情合集中的表情列表 JSON

## 4. WebSocket 事件

### 4.1 客户端发送事件

#### 4.1.1 加入房间

- **事件名**：`join_room`
- **参数**：
  - room: 房间名称
  - username: 用户名

#### 4.1.2 离开房间

- **事件名**：`leave_room`
- **参数**：
  - room: 房间名称
  - username: 用户名

#### 4.1.3 发送消息

- **事件名**：`send_message`
- **参数**：
  - room: 房间名称
  - username: 用户名
  - message: 消息内容

#### 4.1.4 获取消息历史

- **事件名**：`get_message_history`
- **参数**：
  - room: 房间名称
  - username: 用户名

### 4.2 服务器发送事件

#### 4.2.1 新消息

- **事件名**：`new_message`
- **参数**：
  - username: 发送者用户名
  - message: 消息内容
  - timestamp: 时间戳
  - is_self: 是否为自己发送的消息

#### 4.2.2 用户加入

- **事件名**：`user_joined`
- **参数**：
  - username: 加入的用户名
  - message: 系统消息
  - timestamp: 时间戳

#### 4.2.3 用户离开

- **事件名**：`user_left`
- **参数**：
  - username: 离开的用户名
  - message: 系统消息
  - timestamp: 时间戳

#### 4.2.4 用户列表

- **事件名**：`user_list`
- **参数**：
  - room: 房间名称
  - users: 在线用户列表

#### 4.2.5 消息历史

- **事件名**：`message_history`
- **参数**：
  - room: 房间名称
  - messages: 消息历史列表

## 5. 开发流程

### 5.1 环境搭建

1. 克隆项目代码
2. 安装依赖：`pip install -r requirements.txt`
3. 启动开发服务器：`python app.py`
4. 访问 `http://127.0.0.1:5002`

### 5.2 代码规范

- **Python**：遵循 PEP 8 规范
- **JavaScript**：使用 ES6+ 语法
- **CSS**：使用 BEM 命名规范
- **HTML**：使用语义化标签
- **模块化**：遵循单一职责原则，每个模块专注于单一业务领域

### 5.3 模块开发指南

#### 5.3.1 新增业务模块

1. 在 `modules/` 目录下创建新模块目录
2. 创建 `__init__.py`，定义 Blueprint
3. 创建 `routes.py`，定义页面路由
4. 创建 `api.py`，定义 API 接口
5. 在 `app.py` 中注册 Blueprint

#### 5.3.2 新增数据模型

1. 在 `models/` 目录下创建新的模型文件
2. 定义模型类，继承 `db.Model`
3. 在 `models/__init__.py` 中导出模型

#### 5.3.3 新增工具函数

1. 在 `utils/` 目录下创建或编辑工具文件
2. 在 `utils/__init__.py` 中导出函数

### 5.4 测试

- **手动测试**：通过浏览器访问各个功能页面
- **API 测试**：使用 Postman 或类似工具测试 API 接口
- **WebSocket 测试**：使用浏览器开发者工具测试 WebSocket 连接
- **单元测试**：为每个模块编写独立的单元测试

### 5.5 部署

#### 5.5.1 本地部署

```bash
python app.py
```

#### 5.5.2 打包为 EXE

```bash
pyinstaller --onefile --name iFlyCompass app.py
```

#### 5.5.3 生产部署

建议使用 Gunicorn 作为 WSGI 服务器，Nginx 作为反向代理：

```bash
pip install gunicorn

gunicorn -w 4 -b 0.0.0.0:5002 app:app
```

## 6. 常见问题及解决方案

### 6.1 数据库连接问题

- **问题**：无法连接数据库
- **解决方案**：确保 `instance` 目录存在且可写

### 6.2 WebSocket 连接问题

- **问题**：WebSocket 连接失败
- **解决方案**：检查网络连接，确保服务器正在运行

### 6.3 权限问题

- **问题**：无法访问某些页面或功能
- **解决方案**：确保用户具有相应的权限，超级管理员可以在用户管理页面修改权限

### 6.4 Passkey 相关问题

- **问题**：Passkey 无效
- **解决方案**：检查 Passkey 是否已过期或达到最大使用次数

### 6.5 模块导入问题

- **问题**：模块导入失败
- **解决方案**：确保所有模块都正确导出，检查 `__init__.py` 文件

### 6.6 Blueprint 路由冲突

- **问题**：路由冲突或 404 错误
- **解决方案**：检查 Blueprint 的 url_prefix 设置，确保路由定义正确

## 7. 贡献指南

### 7.1 代码提交

1. Fork 项目
2. 创建功能分支
3. 提交代码
4. 创建 Pull Request

### 7.2 代码审查

- 确保代码符合项目规范
- 确保所有测试通过
- 确保文档更新

### 7.3 版本发布

- 遵循语义化版本规范
- 更新 CHANGELOG
- 创建 Git 标签
