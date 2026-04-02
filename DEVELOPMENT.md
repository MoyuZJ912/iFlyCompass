# iFlyCompass 开发文档

## 版本更新

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

### REL1.3.2\_fix1

- **修复**：小说阅读器功能
  - 修复阅读进度记忆功能：添加数据库表存储阅读进度
  - 优化小说列表加载：只在选择小说后加载章节列表
  - 增强用户体验：在小说列表中显示上次读到的章节信息

### REL1.3.2

- **增强**：小说阅读器功能
  - 添加作者显示功能：支持从文件名和文件内容中提取作者信息
  - 添加最新章节显示功能：在小说列表中显示最新章节
  - 改进章节导航功能：添加右侧滑出的章节列表面板
  - 调整布局：将章节导航和切换按钮移到顶部，与小说信息合并
  - 改进错误处理：使用 Element UI 顶部弹出提示替代 alert
  - 整合参考资料中的章节模式：支持多种章节标题格式
  - 添加编码检测功能：自动检测文件编码，支持多种编码格式

### REL1.3.1\_fix1

- **增强**：小说阅读器功能
  - 支持多种编码格式：GBK、GB2312、UTF-16、UTF-8-BOM
  - 增加章节切分规则：如果前20行包含单独一行的"正文"二字，则从它下方第一个有文字的非空行开始计算章节id1

### REL1.3.1

- **修复**：WebSocket重连时产生重复加入消息的问题
- **增强**：小说阅读器功能
  - 修改章节判断规则，支持空行分段和特殊情况处理
  - 添加阅读进度保存功能
  - 实现自动跳转到上次阅读章节
  - 在小说列表中显示阅读进度

## 1. 项目架构

### 1.1 前端架构

- **框架**：Vue.js 2.x
- **UI 库**：Element UI
- **通信**：Socket.IO 客户端
- **构建**：原生 HTML/CSS/JavaScript，无构建工具

### 1.2 后端架构

- **框架**：Flask 2.x
- **数据库**：SQLAlchemy ORM + SQLite
- **认证**：Flask-Login
- **实时通信**：Flask-SocketIO
- **部署**：支持本地开发和 PyInstaller 打包

## 2. 数据库设计

### 2.1 用户表 (User)

| 字段名              | 类型          | 描述             |
| ---------------- | ----------- | -------------- |
| id               | Integer     | 用户 ID，主键       |
| username         | String(50)  | 用户名，唯一         |
| password\_hash   | String(128) | 密码哈希值          |
| is\_super\_admin | Boolean     | 是否为超级管理员       |
| is\_admin        | Boolean     | 是否为管理员         |
| passkey\_used    | String(6)   | 注册时使用的 Passkey |
| created\_at      | DateTime    | 创建时间           |

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

## 3. API 接口

### 3.1 用户相关

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

### 3.5 表情包相关 API

#### 3.5.1 获取表情商城列表

- **URL**：`/api/stickers/hub`
- **方法**：GET
- **权限**：登录用户
- **参数**：
  - type: 表情类型 ('single' 或 'pack')
  - page: 页码（可选）
- **返回**：表情列表 JSON

#### 3.5.2 获取我的表情包

- **URL**：`/api/stickers/mine`
- **方法**：GET
- **权限**：登录用户
- **参数**：
  - type: 表情类型 ('single' 或 'pack')
- **返回**：我的表情包列表 JSON

#### 3.5.3 添加表情包

- **URL**：`/api/stickers/add`
- **方法**：POST
- **权限**：登录用户
- **参数**：
  - code: 表情码
  - type: 表情类型 ('single' 或 'pack')
- **返回**：成功/失败信息 JSON

#### 3.5.4 移除表情包

- **URL**：`/api/stickers/remove`
- **方法**：POST
- **权限**：登录用户
- **参数**：
  - id: 表情包 ID
- **返回**：成功/失败信息 JSON

#### 3.5.5 获取表情包分类

- **URL**：`/api/stickers/categories`
- **方法**：GET
- **权限**：登录用户
- **返回**：表情包分类列表 JSON

#### 3.5.6 获取表情包合集中的表情

- **URL**：`/api/stickers/pack/<code>`
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

### 5.3 测试

- **手动测试**：通过浏览器访问各个功能页面
- **API 测试**：使用 Postman 或类似工具测试 API 接口
- **WebSocket 测试**：使用浏览器开发者工具测试 WebSocket 连接

### 5.4 部署

#### 5.4.1 本地部署

```bash
python app.py
```

#### 5.4.2 打包为 EXE

```bash
pyinstaller --onefile --name iFlyCompass app.py
```

#### 5.4.3 生产部署

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

