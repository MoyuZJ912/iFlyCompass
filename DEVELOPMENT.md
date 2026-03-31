# iFlyCompass 开发文档

## 版本更新

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

| 字段名 | 类型 | 描述 |
|-------|------|------|
| id | Integer | 用户 ID，主键 |
| username | String(50) | 用户名，唯一 |
| password_hash | String(128) | 密码哈希值 |
| is_super_admin | Boolean | 是否为超级管理员 |
| is_admin | Boolean | 是否为管理员 |
| passkey_used | String(6) | 注册时使用的 Passkey |
| created_at | DateTime | 创建时间 |

### 2.2 Passkey 表 (Passkey)

| 字段名 | 类型 | 描述 |
|-------|------|------|
| id | Integer | Passkey ID，主键 |
| key | String(6) | Passkey 值，唯一 |
| duration_days | Integer | 有效期（天数），None 表示无限 |
| max_uses | Integer | 最大使用次数，None 表示无限 |
| current_uses | Integer | 当前使用次数 |
| is_active | Boolean | 是否激活 |
| expires_at | DateTime | 过期时间 |
| created_at | DateTime | 创建时间 |

### 2.3 聊天室表 (ChatRoom)

| 字段名 | 类型 | 描述 |
|-------|------|------|
| id | Integer | 聊天室 ID，主键 |
| name | String(50) | 聊天室名称，唯一 |
| password | String(128) | 密码哈希值，None 表示无密码 |
| created_by | Integer | 创建者 ID，外键关联 User.id |
| created_at | DateTime | 创建时间 |
| is_active | Boolean | 是否激活 |

### 2.4 用户表情包表 (UserSticker)

| 字段名 | 类型 | 描述 |
|-------|------|------|
| id | Integer | 表情包 ID，主键 |
| user_id | Integer | 用户 ID，外键关联 User.id |
| sticker_code | String(20) | 表情码 |
| sticker_type | String(20) | 表情类型 ('single' 或 'pack') |
| sticker_name | String(100) | 表情名称 |
| description | String(255) | 表情描述 |
| local_path | String(255) | 本地缓存路径 |
| created_at | DateTime | 创建时间 |

### 2.5 表情包合集中的表情表 (PackSticker)

| 字段名 | 类型 | 描述 |
|-------|------|------|
| id | Integer | 表情 ID，主键 |
| user_id | Integer | 用户 ID，外键关联 User.id |
| pack_code | String(20) | 所属表情包合集码 |
| sticker_code | String(50) | 表情码 |
| sticker_name | String(100) | 表情名称 |
| description | String(255) | 表情描述 |
| local_path | String(255) | 本地缓存路径 |
| created_at | DateTime | 创建时间 |

## 3. API 接口

### 3.1 用户相关

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