# 文枢

一个轻量、快速的个人文本信息管理与多设备同步工具。支持 PWA 安装到手机主屏幕，体验接近原生 App。

打开即用，发布即同步。在手机上随手记一条想法，电脑上立刻就能看到。

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│   浏览器/PWA  │────▶│  Vercel Edge      │────▶│  PostgreSQL  │
│  (任意设备)   │◀────│  (Serverless API  │◀────│  (Neon DB)   │
│              │     │   + 静态前端)      │     │              │
└──────────────┘     └──────────────────┘     └──────────────┘
```

> **Tech Stack**: React + Tailwind CSS · FastAPI · PostgreSQL (Vercel Postgres/Neon) · Vercel Serverless

## 目录

- [为什么需要它](#为什么需要它)
- [功能特性](#它能做什么)
- [适用场景](#适用场景)
- [技术架构](#技术架构)
- [本地开发](#本地开发)
- [部署到 Vercel](#部署到-vercel)
- [项目结构](#项目结构)
- [使用方法](#使用方法)
- [License](#license)

## 为什么需要它

你有没有这样的经历：

- Mac 上复制了一段文字，想粘贴到 iPhone 上，打开微信发给自己，再从 iPhone 上复制出来
- 公司电脑和个人电脑用的是不同的 Apple ID，AirDrop 用不了，又不想用微信传
- Android 手机上看到一个链接，想在 Mac 上打开，还是得打开微信发给自己
- 微信的"文件传输助手"里塞满了各种零碎的文字、链接、截图，聊天记录越来越乱

**文枢就是为了解决这个问题。** 打开浏览器，粘贴，发送——另一台设备上立刻就能看到。不需要安装任何 App，不需要登录同一个 Apple ID，不需要微信。任何有浏览器的设备都能用。

## 它能做什么

### 快速捕获

打开网页，输入内容，Enter 发送，Shift+Enter 换行。没有复杂的编辑器，没有多余的步骤。页面秒开，操作零延迟。

### 多设备同步

在任何设备的浏览器里打开同一个地址，发布的内容立刻出现在所有设备上。手机上复制一段文字，电脑上直接粘贴——文枢就是你的跨设备剪贴板。

### 智能标签（自动分类）

发布消息时自动识别内容并打标签，无需手动归类：

| 标签 | 触发条件 | 颜色 |
|------|---------|------|
| 网盘 | 包含百度网盘、夸克网盘、阿里云盘、迅雷云盘、天翼云盘链接 | 紫色 |
| 代码 | 多行代码结构（≥3 行，命中率 ≥40%）或单行命令/代码模式 | 绿色 |
| 日记 | 以上均不匹配时的默认标签 | 琥珀色 |

标签栏显示在列表顶部，点击即可按标签筛选，再次点击取消。同一条消息可以拥有多个标签。

### 代码识别与渲染

消息被标记为「代码」后，自动以等宽字体 + 浅灰背景的代码块样式渲染，保留原始格式。识别规则覆盖：

- **多行判定**：Python (`def`/`class`/`import`)、JS (`function`/`const`/`let`)、SQL、HTML 标签、Shell 命令、控制结构等
- **单行判定**：`#!/` shebang、命令行工具 (`git`/`docker`/`pip`/`npm` 等)、管道 `|`、重定向 `>>`、`sudo`、代码操作符 (`=>`/`->`/`===`/`!==`) 等

### 链接识别

消息中的 URL 自动变为可点击的蓝色链接，网盘资源一键直达。

### 消息管理

- **复制** — 点击消息右侧的复制图标，一键复制内容到剪贴板
- **标记已处理** — ○/✓ 切换状态，已处理消息显示灰色背景，一目了然
- **编辑** — ⋯ 菜单 → 编辑，支持就地修改内容，编辑后显示「(已编辑)」标记
- **删除** — ⋯ 菜单 → 删除
- **编辑快捷键** — `⌘+Enter` 保存，`Escape` 取消

### 分页浏览

支持首页、尾页、页码跳转，每页 10 条，大量消息也能流畅浏览。

### 多用户隔离

注册登录后，每个用户拥有独立的私人空间，互不干扰。密码使用 bcrypt 加密存储，认证基于 JWT Token。

### PWA 支持

文枢支持渐进式 Web 应用（PWA），可安装到手机主屏幕：

- **iOS**：Safari 打开 → 分享按钮 → 添加到主屏幕
- **Android**：Chrome 打开 → 自动弹出"安装应用"提示，或菜单 → 添加到主屏幕
- **桌面**：Chrome 地址栏右侧安装图标

安装后体验接近原生 App：独立窗口/全屏、自定义启动图标、主题色状态栏。

Service Worker 缓存策略：
- API 请求：不缓存，直接走网络（保证数据实时性）
- JS/CSS：Network-first（优先网络获取最新版本，离线时回退缓存）
- 静态资源（图标、HTML）：Cache-first（优先缓存，加速加载）

## 适用场景

- **跨设备文本接力** — Mac ↔ iPhone ↔ Android ↔ Windows，任何设备之间快速传递文字和链接。不用微信，不用 AirDrop，不用同一个 Apple ID。打开浏览器就能用
- **告别"文件传输助手"** — 微信的文件传输助手不应该塞满零碎文字。文枢更干净、更快、不污染聊天记录
- **碎片信息收集** — 脑海中闪过的灵感、看到的好文章、值得记住的一句话
- **网盘资源管理** — 自动识别网盘链接，集中管理你的各种下载资源
- **轻量待办** — 发布任务，完成后标记已处理，简单直接
- **个人日记** — 随时随地记录生活碎碎念
- **阅读清单** — 收集想读的文章和链接，读完标记已处理
- **代码片段暂存** — 多行代码自动识别并以代码块样式展示，临时保存命令行和脚本

## 技术架构

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (React)                         │
│  React 19 + Vite + Tailwind CSS 3                          │
│  PWA: manifest.json + Service Worker                        │
├─────────────────────────────────────────────────────────────┤
│                     Vercel 部署平台                          │
│  静态前端 (CDN) + Serverless Functions (Python)              │
├──────────────────────┬──────────────────────────────────────┤
│   本地开发后端        │        生产后端                       │
│   FastAPI + SQLite    │        FastAPI + PostgreSQL          │
│   (backend/main.py)   │        (api/index.py → Neon DB)     │
└──────────────────────┴──────────────────────────────────────┘
```

### 技术选型

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | React 19 + Vite | 组件化 UI，快速热更新 |
| 样式 | Tailwind CSS 3 | 原子化 CSS，响应式设计 |
| 离线 | Service Worker | PWA 缓存，离线可用 |
| 后端 | FastAPI (Python) | 异步高性能 API 框架 |
| 数据库（生产） | PostgreSQL (Neon) | 通过 Vercel Storage 配置 |
| 数据库（本地） | SQLite | 零配置，本地开发即开即用 |
| 认证 | JWT (python-jose) | 无状态 Token 认证 |
| 密码 | bcrypt | 单向加密，安全存储 |
| 部署 | Vercel | 全球 CDN + Serverless + 自动 HTTPS |
| 适配层 | Mangum | ASGI → AWS Lambda 适配（Vercel 运行时） |

### 数据库 Schema

```sql
-- 用户表
CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    DOUBLE PRECISION NOT NULL
);

-- 消息表
CREATE TABLE messages (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id),
    content      TEXT NOT NULL,
    created_at   DOUBLE PRECISION NOT NULL,
    is_processed BOOLEAN NOT NULL DEFAULT FALSE,
    is_edited    BOOLEAN NOT NULL DEFAULT FALSE
);

-- 标签表
CREATE TABLE tags (
    id   SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- 消息-标签关联表（多对多）
CREATE TABLE message_tags (
    message_id INTEGER NOT NULL REFERENCES messages(id),
    tag_id     INTEGER NOT NULL REFERENCES tags(id),
    PRIMARY KEY (message_id, tag_id)
);
```

### API 接口

所有接口以 `/api` 为前缀，需认证的接口在 Header 中携带 `Authorization: Bearer <token>`。

#### 认证

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/register` | 注册（用户名 ≥2 位，密码 ≥4 位） | 否 |
| POST | `/api/login` | 登录 | 否 |
| GET | `/api/me` | 获取当前用户信息 | 是 |

#### 消息

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/messages` | 创建消息（自动检测标签） | 是 |
| GET | `/api/messages` | 分页查询（`?page=1&page_size=10&tag=网盘`） | 是 |
| PUT | `/api/messages/{id}` | 编辑消息内容（重新检测标签，标记 `is_edited`） | 是 |
| PUT | `/api/messages/{id}/process` | 切换已处理/未处理状态 | 是 |
| DELETE | `/api/messages/{id}` | 删除消息（同时删除标签关联） | 是 |

#### 标签

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/tags` | 获取当前用户所有标签及消息数量 | 是 |

#### 调试

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/health` | 健康检查 | 否 |
| GET | `/api/debug` | 数据库连接状态（仅线上） | 否 |

#### 请求/响应示例

**创建消息**

```bash
curl -X POST https://your-domain.vercel.app/api/messages \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"content": "https://pan.baidu.com/s/xxx 提取码: abcd"}'
```

响应：

```json
{
  "id": 1,
  "user_id": 1,
  "username": "demo",
  "content": "https://pan.baidu.com/s/xxx 提取码: abcd",
  "created_at": 1718000000.0,
  "is_processed": false,
  "is_edited": false,
  "tags": ["网盘"]
}
```

**分页查询**

```bash
curl https://your-domain.vercel.app/api/messages?page=1&page_size=10&tag=网盘 \
  -H "Authorization: Bearer <token>"
```

响应：

```json
{
  "items": [...],
  "total": 42,
  "page": 1,
  "page_size": 10,
  "total_pages": 5
}
```

## 本地开发

### 前置条件

- Python 3.9+
- Node.js 18+
- npm

### 一键启动

```bash
./start.sh
```

访问 http://localhost:3000，后端 API 运行在 http://localhost:8000。

### 手动启动

**后端**（FastAPI + SQLite）：

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

**前端**（React + Vite）：

```bash
cd frontend
npm install
npm run dev
```

Vite 开发服务器会将 `/api` 请求代理到后端 `http://127.0.0.1:8000`（配置在 `frontend/vite.config.js`）。

## 部署到 Vercel

### 步骤

1. Fork 或 clone 本仓库
2. 在 [Vercel](https://vercel.com) 导入项目
3. 创建 Vercel Postgres 数据库（Storage → Create → Postgres）
4. 关联数据库到项目（Connect Project）
5. 部署完成，数据库表自动创建

### Vercel 配置

部署配置在 `vercel.json` 中：

- `buildCommand`：`cd frontend && npm install && npm run build`
- `outputDirectory`：`frontend/dist`
- `rewrites`：`/api/*` → `api/index.py`（Serverless Function）

### 环境变量

生产环境会自动注入以下数据库连接变量（无需手动配置，Vercel Postgres 绑定后自动可用）：

- `DATABASE_URL`
- `POSTGRES_URL`
- `POSTGRES_PRISMA_URL`
- `POSTGRES_URL_NON_POOLING`

代码按优先级依次尝试读取这些变量。

### ⚠️ 生产环境注意事项

- 修改 `api/index.py` 中的 `SECRET_KEY` 为随机强密钥
- `backend/` 目录仅用于本地开发，不会部署到 Vercel（已加入 `.gitignore` 排除逻辑和 `vercel.json` 路由配置）

## 项目结构

```
txthub/
├── api/                    # Vercel Serverless 后端
│   ├── index.py            # 全部 API 路由 (FastAPI + PostgreSQL + Mangum)
│   └── requirements.txt    # 生产依赖
├── backend/                # 本地开发后端
│   ├── main.py             # API 路由 (FastAPI + SQLite)
│   └── requirements.txt    # 本地依赖
├── frontend/               # React 前端
│   ├── src/
│   │   ├── App.jsx         # 主界面（认证、消息列表、标签、编辑、分页）
│   │   ├── App.css         # 样式（基本由 Tailwind 处理）
│   │   ├── index.css       # Tailwind 指令
│   │   └── main.jsx        # React 入口
│   ├── public/
│   │   ├── manifest.json   # PWA 清单（应用名、图标、主题色）
│   │   ├── sw.js           # Service Worker（缓存策略）
│   │   ├── icon-192.png    # PWA 图标 192x192
│   │   ├── icon-512.png    # PWA 图标 512x512
│   │   ├── apple-touch-icon.png  # iOS 添加到主屏幕图标
│   │   └── favicon.svg     # 浏览器标签页图标
│   ├── index.html          # HTML 入口（meta 标签、SW 注册）
│   ├── vite.config.js      # Vite 配置（开发代理 /api → localhost:8000）
│   └── package.json        # 前端依赖
├── vercel.json             # Vercel 部署配置（构建命令、路由重写）
├── package.json            # 根构建脚本
├── start.sh                # 本地一键启动脚本
├── .gitignore
└── README.md
```

## 使用方法

### 注册与登录

1. 打开文枢网址，进入登录页面
2. 切换到「注册」标签，输入用户名（≥2 位）和密码（≥4 位）
3. 注册成功后自动登录，Token 存储在浏览器 localStorage 中
4. 之后访问自动登录，点击右上角「退出」可注销

### 发送消息

1. 在顶部输入框输入内容
2. 按 **Enter** 发送，**Shift+Enter** 换行
3. 也可以点击右侧「发布」按钮
4. 发送后自动回到第一页，标签栏自动更新

### 管理消息

- **复制**：点击消息右侧的重叠方块图标
- **标记已处理**：点击 ○ 图标切换为 ✓，已处理消息显示灰色背景
- **编辑**：点击 ⋯ → 编辑，修改后按 ⌘+Enter 保存，Escape 取消
- **删除**：点击 ⋯ → 删除

### 按标签筛选

- 标签栏显示在输入框下方，括号内数字为该标签下的消息数量
- 点击标签筛选，再次点击取消
- 点击「清除筛选」重置

### 安装为 App（PWA）

**iPhone/iPad（Safari）**：
1. 用 Safari 打开文枢网址
2. 点击底部分享按钮（方框+箭头图标）
3. 选择「添加到主屏幕」
4. 主屏幕上出现文枢图标，点击即可全屏使用

**Android（Chrome）**：
1. 用 Chrome 打开文枢网址
2. Chrome 可能自动弹出安装提示，点击「安装」
3. 或点击菜单（⋮）→「添加到主屏幕」

**桌面（Chrome/Edge）**：
1. 打开文枢网址
2. 地址栏右侧出现安装图标，点击安装
3. 文枢将以独立窗口运行

## License

MIT
