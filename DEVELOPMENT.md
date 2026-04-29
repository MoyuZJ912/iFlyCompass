# iFlyCompass 开发文档

## 版本更新

### REL2.4.1

**视频播放器 + B站视频缓存与播放**

- **本地视频播放器**：
  - 支持多种视频格式（MP4、WebM、OGG、MKV、AVI、MOV 等）
  - 使用 Plyr 轻量级播放器，本地化部署
  - Element UI 日间风格，与项目整体风格统一
  - 视频列表、搜索过滤、自适应布局
  - HTTP Range 请求支持，可拖拽进度条
  - 带鱼屏适配，确保控件完整显示
- **B站视频缓存与播放**：
  - 首页推荐视频（热门排行榜）
  - 搜索视频、搜索UP主
  - 查看UP主视频列表
  - 视频下载服务（异步多线程、进度追踪）
  - 客户端实时显示下载进度
  - 默认 480P 画质
  - 音视频自动合并（使用内置 FFmpeg）
  - 封面图片代理（解决防盗链问题）
  - 使用 `bilibili-api-python` 库
  - 使用 `curl_cffi` 请求库（伪装浏览器指纹）
- **新增模块**：
  - `modules/video/__init__.py` - 视频播放器模块定义
  - `modules/video/routes.py` - 视频播放器路由
  - `modules/video/api.py` - 视频 API
  - `modules/bili/__init__.py` - B站视频模块定义
  - `modules/bili/routes.py` - B站播放器路由
  - `modules/bili/api.py` - B站 API
  - `modules/bili/download_service.py` - B站视频下载服务
- **新增页面**：
  - `templates/video_player.html` - 视频播放器页面
  - `templates/bili_player.html` - B站视频页面
- **新增文件**：
  - `assets/css/plyr.min.css` - Plyr 播放器样式
  - `assets/js/plyr.min.js` - Plyr 播放器脚本
  - `tools/ffmpeg/ffmpeg.exe` - FFmpeg 可执行文件
  - `tools/ffmpeg/ffprobe.exe` - FFprobe 可执行文件
- **新增 API**：
  - `GET /api/videos` - 获取视频列表
  - `GET /api/video/<filename>` - 流式播放视频
  - `GET /api/bili/recommend` - 获取首页推荐
  - `GET /api/bili/search` - 搜索视频
  - `GET /api/bili/search_user` - 搜索UP主
  - `GET /api/bili/user_videos/<mid>` - 获取UP主视频
  - `GET /api/bili/video/<bvid>` - 获取视频详情
  - `POST /api/bili/download/<bvid>` - 启动下载
  - `GET /api/bili/progress/<bvid>` - 查询下载进度
  - `GET /api/bili/downloads` - 获取所有下载任务
  - `GET /api/bili/cached` - 获取已缓存视频
  - `DELETE /api/bili/delete/<bvid>` - 删除缓存视频
  - `GET /api/bili/play/<bvid>` - 播放缓存视频
  - `GET /api/bili/cover` - 封面图片代理
- **新增依赖**：
  - `bilibili-api-python` - B站 API 库
  - `curl_cffi` - 请求库（支持 TLS 指纹伪装）

### REL2.3.1

**Drop 功能 + 聊天室多人优化 + 导航配置**

- **Drop 功能**：
  - 允许用户向所有用户发送 Drop 消息（气泡形式弹出）
  - 个人冷却 10 分钟，全服冷却 1 分钟
  - HTTP 轮询每 10 秒查询一次最新 Drop
  - 气泡显示发送者昵称和消息内容
  - 支持屏蔽用户（黑名单管理）
  - Drop 设置页面：开关接收、黑名单管理、快捷发送
  - 使用 localStorage 记录 lastId，切换页面不重复显示
- **聊天室多人优化模式**：
  - 聊天室创建者可开启"多人优化"模式
  - 列表模式显示：所有发言人都在左侧，消息内容对齐
  - 交替背景色区分不同消息行
  - 连续同用户消息隐藏昵称（保留占位）
  - 自己发送的消息用户名标蓝加粗
  - 引用消息格式：`[用户名] 消息内容`
  - 表情包和引用消息适配列表模式
- **导航配置功能**：
  - 启动时自动创建 `instance/nav.yml` 配置文件
  - 支持通过 YAML 配置添加自定义导航项
  - 导航项自动显示在小工具/小游戏页面
  - 支持外部链接（新标签页打开）和相对链接
- **新增模块**：
  - `modules/drop/__init__.py` - Drop 模块定义
  - `modules/drop/routes.py` - Drop 设置页面路由
  - `modules/drop/api.py` - Drop API
- **新增模型**：
  - `models/drop.py` - DropMessage, DropSettings, DropBlacklist 模型
- **新增页面**：
  - `templates/drop_settings.html` - Drop 设置页面
- **新增工具**：
  - `utils/nav.py` - 导航配置工具
- **新增文件**：
  - `assets/js/drop.js` - Drop 前端脚本
  - `assets/css/drop.css` - Drop 样式
- **新增 API**：
  - `POST /api/drop/send` - 发送 Drop
  - `GET /api/drop/poll` - 轮询 Drop
  - `GET /api/drop/status` - 获取冷却状态
  - `GET /api/drop/settings` - 获取 Drop 设置
  - `PUT /api/drop/settings` - 更新 Drop 设置
  - `POST /api/drop/blacklist` - 添加黑名单
  - `DELETE /api/drop/blacklist` - 移除黑名单
  - `GET /api/drop/users/search` - 搜索用户
  - `GET /api/nav/items` - 获取导航项
- **数据库变更**：
  - 新增 `drop_message` 表
  - 新增 `drop_settings` 表
  - 新增 `drop_blacklist` 表
  - ChatRoom 表新增 `multi_user_mode` 字段

### REL2.3.0

**公告系统**

- **公告类型**：
  - 横幅公告：在控制台首页标题栏下方显示，同时只能存在一个
  - 通知公告：支持弹窗提醒，可存在多个
- **公告优先级**：
  - 重要：红色背景，无法关闭，每次进入控制台弹出（通知公告）
  - 一般：黄色背景，可确认或不再提示
  - 次要：蓝色背景，仅在公告中心显示
- **样式设计**：
  - 重要公告：背景色 `#fef0f0`，字体色 `#f56c6c`
  - 一般公告：背景色 `#fdf6ec`，字体色 `#e6a23c`
  - 次要公告：背景色 `#ecf5ff`，字体色 `#409eff`
  - 使用 Element UI Tag 配色方案
- **弹窗逻辑**：
  - 多条未读通知时显示数量，点击跳转公告中心
  - 单条通知显示完整内容，标题加粗，分隔线区分正文
  - 重要通知可关闭但下次仍弹出
  - 一般通知确认后本次会话不再弹出
- **角标显示**：
  - 感叹号：有重要公告
  - 数字：有未确认的一般公告数量
  - 红点：有未读的次要公告
- **权限控制**：
  - 超级管理员：可创建所有类型公告
  - 管理员：可创建一般横幅、一般通知、次要通知
  - 普通用户：无管理权限
- **新增模块**：
  - `modules/announcement/__init__.py` - 公告模块定义
  - `modules/announcement/routes.py` - 公告页面路由
  - `modules/announcement/api.py` - 公告 API
- **新增模型**：
  - `models/announcement.py` - Announcement, UserAnnouncementStatus 模型
- **新增页面**：
  - `templates/announcement_manage.html` - 公告管理页面
  - `templates/announcement_center.html` - 公告中心页面
- **新增 API**：
  - `GET /api/announcements` - 获取所有公告
  - `GET /api/announcements/banner` - 获取横幅公告
  - `GET /api/announcements/notifications/popup` - 获取弹窗通知
  - `GET /api/announcements/badge` - 获取公告角标状态
  - `POST /api/announcements/<id>/dismiss` - 关闭公告
  - `POST /api/announcements/<id>/confirm` - 确认公告
  - `POST /api/announcements/<id>/never-show` - 不再提示
  - `GET /api/announcements/manage` - 获取所有公告（管理）
  - `POST /api/announcements/manage` - 创建公告
  - `PUT /api/announcements/manage/<id>` - 更新公告
  - `DELETE /api/announcements/manage/<id>` - 删除公告
- **数据库变更**：
  - 新增 `announcement` 表
  - 新增 `user_announcement_status` 表

### REL2.2.1

**沉浸式阅读器优化 + 音乐播放器优化**

- **沉浸式阅读器分页优化**：
  - 所有设备统一应用高 DPI 优化（减少 5% 行数和字符数）
  - 每页行数额外减少 3 行，进一步防止文字溢出边界
  - 添加续段处理：被截断到新页面的内容标记为续段
  - 续段内容不缩进，直接紧贴开头显示
  - 正常段落保持首行缩进 2em（空两格）
- **音乐播放器搜索优化**：
  - 搜索结果即时显示，无需等待封面加载
  - 封面图片后台异步分批加载（每批 10 张）
  - 使用本地缓存路径直接显示，加载失败时显示默认图片
  - 移除封面加载进度显示，提升用户体验

### REL2.2.0

**系统设置 + 配置重构**

- **系统设置模块**：
  - 新增 `modules/settings/` 系统设置模块
  - 管理员/超级管理员可在系统设置页面配置各项功能
  - 支持通用设置和安全设置两大分类
- **通用设置**：
  - 首页显示设置：切换显示昵称或用户名
  - 用户设置：允许设置昵称、昵称长度限制（5-20字）
  - 导航设置：导航栏默认展开、工具/游戏卡片布局（1×3、1×4、2×3）
- **安全设置**：
  - 用户名设置：手动添加和自助注册的用户名长度限制
  - 密码设置：密码强度要求（4个等级）、允许弱密码、允许改密码
  - 安全问题：允许自助找回密码、设置安全问题
- **忘记密码功能**：
  - 登录页面添加"忘记密码"链接
  - 三步验证流程：输入用户名 → 回答安全问题 → 重置密码
  - 支持通过安全问题自助重置密码
- **个人设置增强**：
  - 根据系统设置动态显示/隐藏昵称输入框
  - 根据系统设置控制密码修改权限
  - 安全问题设置（启用自助找回密码后可见）
- **注册验证增强**：
  - 用户名长度验证（根据系统设置）
  - 密码强度验证（根据系统设置）
  - 弱密码检测
- **用户管理验证**：
  - 手动添加用户时的用户名长度验证
  - 昵称设置验证
- **配置文件重构**：
  - 删除 `config.py` 中的硬编码配置
  - 新增 `instance/config.yml` YAML 配置文件
  - 系统设置与 Flask 配置统一存储在 YAML 文件中
  - 删除 `instance/system_settings.json`，合并到 config.yml
  - 添加 PyYAML 依赖
- **新增文件**：
  - `modules/settings/__init__.py` - 系统设置模块定义
  - `modules/settings/routes.py` - 系统设置页面路由
  - `modules/settings/api.py` - 系统设置 API
  - `templates/system_settings.html` - 系统设置页面
  - `templates/forgot_password.html` - 忘记密码页面
  - `utils/system_settings.py` - 系统设置工具（从 YAML 读取）
  - `utils/validators.py` - 验证工具（密码强度、用户名、昵称）
  - `instance/config.yml` - YAML 配置文件
- **新增 API**：
  - `GET /api/settings` - 获取所有系统设置
  - `PUT /api/settings/general` - 更新通用设置
  - `PUT /api/settings/security` - 更新安全设置
  - `POST /api/settings/reset` - 重置设置为默认值
  - `POST /api/auth/forgot-password/check` - 检查用户名
  - `POST /api/auth/forgot-password/verify` - 验证安全问题答案
  - `POST /api/auth/forgot-password/reset` - 重置密码
- **数据库变更**：
  - User 表新增 `security_question` 字段
  - User 表新增 `security_answer_hash` 字段

### REL2.1.3

**手势防御系统 + 随身听优化**

- **防御层 5：absolute 定位 + body 缓冲垫**：
  - 解决宿主 App 全局手势劫持页面滚动的问题
  - 通过 `#touch-buffer` 元素创建可滚动的 body 区域
  - 欺骗浏览器认为页面可滚动，从而让内部内容区域正常滚动
  - 支持四方向滚动（上、下、左、右）
  - 侧边栏和标题栏通过反向 transform 固定位置
- **CSS 实现**：
  - `html.touch-defense-5`：禁用 overscroll-behavior
  - `body.touch-defense-5`：设置 overflow: auto，允许滚动
  - `.touch-defense-5 #scroll-wrap`：absolute 定位，跟随 body 滚动
  - `.touch-defense-5 .console-content`：设置 touch-action: pan-x pan-y
- **JavaScript 滚动同步**：
  - 监听 window scroll 事件
  - 主容器通过 transform 跟随 body 滚动
  - 侧边栏和标题栏通过反向 transform 固定位置
- **滑动测试页面**：
  - 新增 `/board/swipe-test` 路由
  - 仅管理员和超级管理员可访问
  - 从用户下拉菜单进入（个人设置下方）
  - 测试四方向滑动功能
- **随身听优化**：
  - 搜索结果调用 `/api/ncm/song/detail` 获取完整歌曲信息
  - 修复搜索结果封面显示默认图片、歌手显示未知的问题
  - 新增封面缓存 API `/api/ncm/cache-cover`
  - 移除播放列表功能，改为单曲播放模式
  - 点击新歌曲时替换当前播放的歌曲
- **新增 API**：
  - `POST /api/ncm/cache-cover` - 缓存封面图片
  - `GET /music/cache/covers/<filename>` - 提供缓存的封面文件
- **新增文件**：
  - `templates/swipe_test.html` - 滑动测试页面

### EVA2.1.2

**沉浸式阅读器兼容性修复**

- **修复分页逻辑bug**：
  - 修复第一章第一页标题和正文重叠的问题
  - 优化 `while` 循环中的分页逻辑，正确处理标题占用空间
  - 分页后正确计算剩余内容行数
- **低版本 WebView 兼容性处理**：
  - 检测 `localStorage` 是否存在，不存在则创建 mock 对象
  - 检测 `localStorage` 是否可用，失败则替换为 mock
  - 提供 `getItem`, `setItem`, `removeItem`, `clear` 方法
  - 解决旧版 WebView 中 `Cannot read property 'getItem' of null` 错误
- **ES5 语法兼容**：
  - 将所有箭头函数 `=>` 替换为传统 `function` 语法
  - 将 `const`/`let` 替换为 `var`
  - 将模板字符串 `` `...${}...` `` 替换为字符串拼接
  - 将 `for...of` 循环替换为传统 `for` 循环
  - 将可选链操作符 `?.` 替换为 `&&` 判断
  - 将对象展开运算符 `{ ...obj }` 替换为逐个属性赋值

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
  - **modules/** - modules/ - 业务模块层
    - auth/：用户认证模块（登录、注册、用户管理、Passkey 管理）
    - chat/：聊天室模块（聊天室管理、WebSocket 事件处理）
    - novel/：小说阅读器模块（小说列表、章节解析、阅读进度）
    - sticker/：表情包管理模块（表情商城、个人收藏、表情包合集）
    - main/：主页面模块（首页、控制面板、工具页面）
    - drop/：Drop 消息模块（Drop 消息发送、接收、设置）
- **代码质量提升**：
  - 配置集中管理（config.py）
  - 扩展统一初始化（extensions.py）
  - 清晰的模块边界和职责划分
  - 更好的代码复用性

### REL1.3.4\_fix1

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
- **ncm 模块**：随身听
  - routes.py：播放器页面路由
  - api.py：网易云音乐 API
- **video 模块**：视频播放器
  - routes.py：播放器页面路由
  - api.py：视频流 API
- **bili 模块**：B站视频
  - routes.py：播放器页面路由
  - api.py：B站 API
  - download_service.py：视频下载服务
- **main 模块**：主页面
  - routes.py：首页、控制面板、工具页面
- **settings 模块**：系统设置
  - routes.py：系统设置页面路由
  - api.py：系统设置 API
- **announcement 模块**：公告系统
  - routes.py：公告中心页面路由
  - api.py：公告管理 API

#### 1.3.3 数据模型层

独立的数据模型层，按业务领域组织：

- **user.py**：User, Passkey
- **chat.py**：ChatRoom
- **sticker.py**：UserSticker, PackSticker
- **novel.py**：NovelReadingProgress
- **announcement.py**：Announcement, UserAnnouncementStatus
- **drop.py**：DropMessage, DropSettings, DropBlacklist

#### 1.3.4 工具函数层

统一的工具函数层，提供通用功能：

- **common.py**：
  - get\_bing\_wallpaper()：获取必应壁纸
  - get\_poetry()：获取今日诗词
  - generate\_passkey()：生成 Passkey
  - get\_utc\_plus\_8\_time()：获取 UTC+8 时间
- **file.py**：
  - detect\_file\_encoding()：检测文件编码
  - read\_novel\_content()：读取小说内容
  - download\_sticker\_image()：下载表情包图片
- **chapter\_parser.py**：
  - parse\_chapters\_advanced()：高级章节解析，返回章节列表
  - detect\_chapters()：从文件检测章节位置
  - detect\_chapters\_from\_lines()：从行列表检测章节
  - V3.1 锚点学习 + 统计验证算法
- **system\_settings.py**：
  - get\_settings()：获取系统设置
  - update\_settings()：更新系统设置
  - 从 YAML 配置文件读取系统设置
- **validators.py**：
  - validate\_password\_strength()：验证密码强度
  - is\_weak\_password()：检查是否为弱密码
  - validate\_username()：验证用户名
  - validate\_nickname()：验证昵称
- **nav.py**：
  - init\_nav\_file()：初始化导航配置文件
  - get\_nav\_items()：获取导航项列表

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

| 字段名                    | 类型          | 描述             |
| ---------------------- | ----------- | -------------- |
| id                     | Integer     | 用户 ID，主键       |
| username               | String(50)  | 用户名，唯一         |
| nickname               | String(50)  | 昵称（可选）         |
| password\_hash         | String(128) | 密码哈希值          |
| is\_super\_admin       | Boolean     | 是否为超级管理员       |
| is\_admin              | Boolean     | 是否为管理员         |
| passkey\_used          | String(6)   | 注册时使用的 Passkey |
| security\_question     | String(255) | 安全问题（可选）       |
| security\_answer\_hash | String(128) | 安全问题答案哈希（可选）   |
| created\_at            | DateTime    | 创建时间           |

### 2.2 Passkey 表 (Passkey)

| 字段名            | 类型        | 描述                |
| -------------- | --------- | ----------------- |
| id             | Integer   | Passkey ID，主键     |
| key            | String(6) | Passkey 值，唯一      |
| duration\_days | Integer   | 有效期（天数），None 表示无限 |
| max\_uses      | Integer   | 最大使用次数，None 表示无限  |
| current\_uses  | Integer   | 当前使用次数            |
| is\_active     | Boolean   | 是否激活              |
| expires\_at    | DateTime  | 过期时间              |
| created\_at    | DateTime  | 创建时间              |

### 2.3 聊天室表 (ChatRoom)

| 字段名         | 类型          | 描述                  |
| ----------- | ----------- | ------------------- |
| id          | Integer     | 聊天室 ID，主键           |
| name        | String(50)  | 聊天室名称，唯一            |
| password    | String(128) | 密码哈希值，None 表示无密码    |
| created\_by | Integer     | 创建者 ID，外键关联 User.id |
| created\_at | DateTime    | 创建时间                |
| is\_active  | Boolean     | 是否激活                |

### 2.4 用户表情包表 (UserSticker)

| 字段名           | 类型          | 描述                       |
| ------------- | ----------- | ------------------------ |
| id            | Integer     | 表情包 ID，主键                |
| user\_id      | Integer     | 用户 ID，外键关联 User.id       |
| sticker\_code | String(20)  | 表情码                      |
| sticker\_type | String(20)  | 表情类型 ('single' 或 'pack') |
| sticker\_name | String(100) | 表情名称                     |
| description   | String(255) | 表情描述                     |
| local\_path   | String(255) | 本地缓存路径                   |
| created\_at   | DateTime    | 创建时间                     |

### 2.5 表情包合集中的表情表 (PackSticker)

| 字段名           | 类型          | 描述                 |
| ------------- | ----------- | ------------------ |
| id            | Integer     | 表情 ID，主键           |
| user\_id      | Integer     | 用户 ID，外键关联 User.id |
| pack\_code    | String(20)  | 所属表情包合集码           |
| sticker\_code | String(50)  | 表情码                |
| sticker\_name | String(100) | 表情名称               |
| description   | String(255) | 表情描述               |
| local\_path   | String(255) | 本地缓存路径             |
| created\_at   | DateTime    | 创建时间               |

### 2.6 小说阅读进度表 (NovelReadingProgress)

| 字段名                  | 类型          | 描述                 |
| -------------------- | ----------- | ------------------ |
| id                   | Integer     | 进度 ID，主键           |
| user\_id             | Integer     | 用户 ID，外键关联 User.id |
| novel\_filename      | String(255) | 小说文件名              |
| last\_chapter\_index | Integer     | 最后阅读的章节索引          |
| last\_read\_at       | DateTime    | 最后阅读时间             |

### 2.7 公告表 (Announcement)

| 字段名                | 类型          | 描述                                |
| ------------------ | ----------- | --------------------------------- |
| id                 | Integer     | 公告 ID，主键                          |
| title              | String(200) | 公告标题                              |
| content            | Text        | 公告内容                              |
| announcement\_type | String(20)  | 公告类型（'banner' 或 'notification'）   |
| priority           | String(20)  | 优先级（'important'、'normal'、'minor'） |
| created\_by        | Integer     | 创建者 ID，外键关联 User.id               |
| created\_at        | DateTime    | 创建时间                              |
| updated\_at        | DateTime    | 更新时间                              |
| is\_active         | Boolean     | 是否激活                              |

### 2.8 用户公告状态表 (UserAnnouncementStatus)

| 字段名                | 类型       | 描述                         |
| ------------------ | -------- | -------------------------- |
| id                 | Integer  | 状态 ID，主键                   |
| user\_id           | Integer  | 用户 ID，外键关联 User.id         |
| announcement\_id   | Integer  | 公告 ID，外键关联 Announcement.id |
| is\_dismissed      | Boolean  | 是否永久关闭                     |
| dismissed\_at      | DateTime | 关闭时间                       |
| session\_dismissed | Boolean  | 本次会话是否已关闭                  |

### 2.9 Drop 消息表 (DropMessage)

| 字段名          | 类型          | 描述                  |
| ------------ | ----------- | ------------------- |
| id           | Integer     | 消息 ID，主键            |
| sender\_id   | Integer     | 发送者 ID，外键关联 User.id |
| sender\_name | String(50)  | 发送者昵称               |
| content      | String(200) | 消息内容                |
| created\_at  | DateTime    | 创建时间                |

### 2.10 Drop 设置表 (DropSettings)

| 字段名            | 类型       | 描述                 |
| -------------- | -------- | ------------------ |
| id             | Integer  | 设置 ID，主键           |
| user\_id       | Integer  | 用户 ID，外键关联 User.id |
| enabled        | Boolean  | 是否接收 Drop 消息       |
| last\_drop\_at | DateTime | 最后发送时间             |

### 2.11 Drop 黑名单表 (DropBlacklist)

| 字段名               | 类型       | 描述                    |
| ----------------- | -------- | --------------------- |
| id                | Integer  | 记录 ID，主键              |
| user\_id          | Integer  | 用户 ID，外键关联 User.id    |
| blocked\_user\_id | Integer  | 被屏蔽用户 ID，外键关联 User.id |
| created\_at       | DateTime | 创建时间                  |

## 3. API 接口

### 3.1 用户认证相关

#### 3.1.1 注册

- **URL**：`/register`
- **方法**：POST
- **参数**：
  - username: 用户名
  - password: 密码
  - confirm\_password: 确认密码
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
  - is\_admin: 是否为管理员（仅超级管理员可设置）
- **返回**：新用户信息 JSON

#### 3.2.3 更新用户

- **URL**：`/api/users`
- **方法**：PUT
- **权限**：管理员或超级管理员
- **参数**：
  - id: 用户 ID
  - password: 密码（可选）
  - is\_admin: 是否为管理员（仅超级管理员可设置）
- **返回**：更新后的用户信息 JSON

#### 3.2.4 删除用户

- **URL**：`/api/users`
- **方法**：DELETE
- **权限**：管理员或超级管理员
- **参数**：
  - id: 用户 ID
- **返回**：成功/失败信息 JSON

#### 3.2.5 获取个人资料

- **URL**：`/api/user/profile`
- **方法**：GET
- **权限**：登录用户
- **返回**：用户资料 JSON（包含系统设置相关权限）

#### 3.2.6 更新个人资料

- **URL**：`/api/user/profile`
- **方法**：PUT
- **权限**：登录用户
- **参数**：
  - nickname: 昵称（可选）
  - password: 新密码（可选）
  - security\_question: 安全问题（可选）
  - security\_answer: 安全问题答案（可选）
- **返回**：成功/失败信息 JSON

#### 3.2.7 忘记密码 - 检查用户名

- **URL**：`/api/auth/forgot-password/check`
- **方法**：POST
- **权限**：公开
- **参数**：
  - username: 用户名
- **返回**：安全问题 JSON

#### 3.2.8 忘记密码 - 验证答案

- **URL**：`/api/auth/forgot-password/verify`
- **方法**：POST
- **权限**：公开
- **参数**：
  - username: 用户名
  - answer: 安全问题答案
- **返回**：成功/失败信息 JSON

#### 3.2.9 忘记密码 - 重置密码

- **URL**：`/api/auth/forgot-password/reset`
- **方法**：POST
- **权限**：公开
- **参数**：
  - username: 用户名
  - answer: 安全问题答案
  - new\_password: 新密码
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
  - duration\_days: 有效期（天数，可选）
  - max\_uses: 最大使用次数（可选）
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
  - room\_id: 聊天室 ID
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
  - chapter\_index: 章节索引
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

### 3.7 系统设置相关 API

#### 3.7.1 获取系统设置

- **URL**：`/api/settings`
- **方法**：GET
- **权限**：管理员或超级管理员
- **返回**：系统设置 JSON（包含 general、security、password\_strength\_options、card\_layout\_options）

#### 3.7.2 更新通用设置

- **URL**：`/api/settings/general`
- **方法**：PUT
- **权限**：管理员或超级管理员
- **参数**：
  - home\_display: 首页显示（'nickname' 或 'username'）
  - allow\_nickname: 是否允许设置昵称
  - nickname\_min\_length: 昵称最小长度
  - nickname\_max\_length: 昵称最大长度
  - sidebar\_default\_expanded: 导航栏默认展开
  - card\_layout: 卡片布局（'1x3'、'1x4'、'2x3'）
- **返回**：成功/失败信息 JSON

#### 3.7.3 更新安全设置

- **URL**：`/api/settings/security`
- **方法**：PUT
- **权限**：管理员或超级管理员（超级管理员可修改所有设置，管理员只能修改部分）
- **参数**：
  - username\_manual\_min: 手动添加用户名最小长度（仅超管）
  - username\_manual\_max: 手动添加用户名最大长度（仅超管）
  - username\_register\_min: 自助注册用户名最小长度
  - username\_register\_max: 自助注册用户名最大长度
  - password\_strength: 密码强度（1-4）
  - allow\_weak\_password: 是否允许弱密码
  - allow\_self\_password\_reset: 是否允许自助找回密码
  - allow\_change\_password: 是否允许改密码
- **返回**：成功/失败信息 JSON

#### 3.7.4 重置系统设置

- **URL**：`/api/settings/reset`
- **方法**：POST
- **权限**：超级管理员
- **返回**：成功/失败信息 JSON

### 3.8 随身听相关 API

#### 3.8.1 搜索歌曲

- **URL**：`/api/ncm/search`
- **方法**：GET
- **权限**：登录用户
- **参数**：
  - keywords: 搜索关键词
  - limit: 返回数量（可选，默认 30）
- **返回**：歌曲列表 JSON

#### 3.8.2 获取歌曲详情

- **URL**：`/api/ncm/song/detail`
- **方法**：GET
- **权限**：登录用户
- **参数**：
  - ids: 歌曲 ID（多个用逗号分隔）
- **返回**：歌曲详情列表 JSON

#### 3.8.3 获取歌曲播放地址

- **URL**：`/api/ncm/song/url`
- **方法**：GET
- **权限**：登录用户
- **参数**：
  - id: 歌曲 ID
- **返回**：播放地址 JSON

#### 3.8.4 获取推荐歌单

- **URL**：`/api/ncm/personalized`
- **方法**：GET
- **权限**：登录用户
- **参数**：
  - limit: 返回数量（可选，默认 10）
- **返回**：推荐歌单列表 JSON

#### 3.8.5 获取热搜列表

- **URL**：`/api/ncm/hot-search`
- **方法**：GET
- **权限**：登录用户
- **返回**：热搜列表 JSON

#### 3.8.6 获取歌单详情

- **URL**：`/api/ncm/playlist/detail`
- **方法**：GET
- **权限**：登录用户
- **参数**：
  - id: 歌单 ID
- **返回**：歌单详情 JSON

#### 3.8.7 缓存音乐到本地

- **URL**：`/api/ncm/cache-music`
- **方法**：POST
- **权限**：登录用户
- **参数**：
  - id: 歌曲 ID
- **返回**：缓存文件路径 JSON

#### 3.8.8 缓存封面图片

- **URL**：`/api/ncm/cache-cover`
- **方法**：POST
- **权限**：登录用户
- **参数**：
  - url: 封面图片 URL
- **返回**：缓存文件路径 JSON

#### 3.8.9 获取缓存的音乐文件

- **URL**：`/music/<filename>`
- **方法**：GET
- **权限**：登录用户
- **返回**：音乐文件

#### 3.8.10 获取缓存的封面文件

- **URL**：`/music/cache/covers/<filename>`
- **方法**：GET
- **权限**：登录用户
- **返回**：封面图片文件

### 3.9 视频播放器相关 API

#### 3.9.1 获取视频列表

- **URL**：`/api/videos`
- **方法**：GET
- **权限**：登录用户
- **返回**：视频列表 JSON（name, size, size\_display）

#### 3.9.2 流式播放视频

- **URL**：`/api/video/<filename>`
- **方法**：GET
- **权限**：登录用户
- **返回**：视频文件流（支持 HTTP Range 请求）

### 3.10 B站视频相关 API

#### 3.10.1 获取首页推荐

- **URL**：`/api/bili/recommend`
- **方法**：GET
- **权限**：登录用户
- **返回**：推荐视频列表 JSON

#### 3.10.2 搜索视频

- **URL**：`/api/bili/search`
- **方法**：GET
- **权限**：登录用户
- **参数**：
  - keyword: 搜索关键词
  - page: 页码（可选）
- **返回**：搜索结果 JSON

#### 3.10.3 搜索UP主

- **URL**：`/api/bili/search_user`
- **方法**：GET
- **权限**：登录用户
- **参数**：
  - keyword: 搜索关键词
  - page: 页码（可选）
- **返回**：UP主列表 JSON

#### 3.10.4 获取UP主视频

- **URL**：`/api/bili/user_videos/<mid>`
- **方法**：GET
- **权限**：登录用户
- **参数**：
  - page: 页码（可选）
  - ps: 每页数量（可选）
- **返回**：UP主视频列表 JSON

#### 3.10.5 获取视频详情

- **URL**：`/api/bili/video/<bvid>`
- **方法**：GET
- **权限**：登录用户
- **返回**：视频详情 JSON

#### 3.10.6 启动下载

- **URL**：`/api/bili/download/<bvid>`
- **方法**：POST
- **权限**：登录用户
- **返回**：下载任务信息 JSON

#### 3.10.7 查询下载进度

- **URL**：`/api/bili/progress/<bvid>`
- **方法**：GET
- **权限**：登录用户
- **返回**：下载进度 JSON

#### 3.10.8 获取所有下载任务

- **URL**：`/api/bili/downloads`
- **方法**：GET
- **权限**：登录用户
- **返回**：下载任务列表 JSON

#### 3.10.9 获取已缓存视频

- **URL**：`/api/bili/cached`
- **方法**：GET
- **权限**：登录用户
- **返回**：已缓存视频列表 JSON

#### 3.10.10 删除缓存视频

- **URL**：`/api/bili/delete/<bvid>`
- **方法**：DELETE
- **权限**：登录用户
- **返回**：成功/失败信息 JSON

#### 3.10.11 播放缓存视频

- **URL**：`/api/bili/play/<bvid>`
- **方法**：GET
- **权限**：登录用户
- **返回**：视频文件流

#### 3.10.12 封面图片代理

- **URL**：`/api/bili/cover`
- **方法**：GET
- **权限**：登录用户
- **参数**：
  - url: 封面图片 URL
- **返回**：图片文件

### 3.11 公告相关 API

#### 3.11.1 获取所有公告

- **URL**：`/api/announcements`
- **方法**：GET
- **权限**：登录用户
- **参数**：
  - type: 公告类型（'all'、'banner'、'notification'，可选，默认 'all'）
- **返回**：公告列表 JSON（包含用户阅读状态）

#### 3.11.2 获取横幅公告

- **URL**：`/api/announcements/banner`
- **方法**：GET
- **权限**：登录用户
- **返回**：当前激活的横幅公告 JSON

#### 3.11.3 获取弹窗通知

- **URL**：`/api/announcements/notifications/popup`
- **方法**：GET
- **权限**：登录用户
- **返回**：需要弹窗显示的通知公告列表 JSON

#### 3.11.4 获取公告角标状态

- **URL**：`/api/announcements/badge`
- **方法**：GET
- **权限**：登录用户
- **返回**：角标状态 JSON（type: 'exclamation'/'number'/'dot'/'none'，count: 数字）

#### 3.11.5 关闭公告

- **URL**：`/api/announcements/<id>/dismiss`
- **方法**：POST
- **权限**：登录用户
- **返回**：成功/失败信息 JSON

#### 3.11.6 确认公告

- **URL**：`/api/announcements/<id>/confirm`
- **方法**：POST
- **权限**：登录用户
- **返回**：成功/失败信息 JSON

#### 3.11.7 不再提示

- **URL**：`/api/announcements/<id>/never-show`
- **方法**：POST
- **权限**：登录用户
- **返回**：成功/失败信息 JSON

#### 3.11.8 获取所有公告（管理）

- **URL**：`/api/announcements/manage`
- **方法**：GET
- **权限**：管理员或超级管理员
- **返回**：所有公告列表 JSON

#### 3.11.9 创建公告

- **URL**：`/api/announcements/manage`
- **方法**：POST
- **权限**：管理员或超级管理员
- **参数**：
  - title: 公告标题
  - content: 公告内容
  - announcement\_type: 公告类型（'banner' 或 'notification'）
  - priority: 优先级（'important'、'normal'、'minor'）
- **返回**：新公告信息 JSON

#### 3.11.10 更新公告

- **URL**：`/api/announcements/manage/<id>`
- **方法**：PUT
- **权限**：管理员或超级管理员
- **参数**：
  - title: 公告标题（可选）
  - content: 公告内容（可选）
  - priority: 优先级（可选）
- **返回**：更新后的公告信息 JSON

#### 3.11.11 删除公告

- **URL**：`/api/announcements/manage/<id>`
- **方法**：DELETE
- **权限**：管理员或超级管理员
- **返回**：成功/失败信息 JSON

### 3.12 Drop 相关 API

#### 3.12.1 发送 Drop

- **URL**：`/api/drop/send`
- **方法**：POST
- **权限**：登录用户
- **参数**：
  - content: 消息内容（最多 200 字）
- **返回**：Drop 信息 JSON

#### 3.12.2 轮询 Drop

- **URL**：`/api/drop/poll`
- **方法**：GET
- **权限**：登录用户
- **参数**：
  - last\_id: 上次获取的最后 ID（可选）
- **返回**：新 Drop 列表 JSON

#### 3.12.3 获取冷却状态

- **URL**：`/api/drop/status`
- **方法**：GET
- **权限**：登录用户
- **返回**：冷却状态 JSON（global\_cooldown, user\_cooldown, can\_send）

#### 3.12.4 获取 Drop 设置

- **URL**：`/api/drop/settings`
- **方法**：GET
- **权限**：登录用户
- **返回**：Drop 设置 JSON（enabled, blocked\_users）

#### 3.12.5 更新 Drop 设置

- **URL**：`/api/drop/settings`
- **方法**：PUT
- **权限**：登录用户
- **参数**：
  - enabled: 是否接收 Drop 消息
- **返回**：成功/失败信息 JSON

#### 3.12.6 添加黑名单

- **URL**：`/api/drop/blacklist`
- **方法**：POST
- **权限**：登录用户
- **参数**：
  - user\_id: 要屏蔽的用户 ID
- **返回**：成功/失败信息 JSON

#### 3.12.7 移除黑名单

- **URL**：`/api/drop/blacklist`
- **方法**：DELETE
- **权限**：登录用户
- **参数**：
  - user\_id: 要解除屏蔽的用户 ID
- **返回**：成功/失败信息 JSON

#### 3.12.8 搜索用户

- **URL**：`/api/drop/users/search`
- **方法**：GET
- **权限**：登录用户
- **参数**：
  - keyword: 搜索关键词
- **返回**：用户列表 JSON

### 3.13 导航相关 API

#### 3.13.1 获取导航项

- **URL**：`/api/nav/items`
- **方法**：GET
- **权限**：登录用户
- **参数**：
  - category: 分类（'tools' 或 'games'）
- **返回**：导航项列表 JSON

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
  - is\_self: 是否为自己发送的消息

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
- **解决方案**：检查 Blueprint 的 url\_prefix 设置，确保路由定义正确

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

