# 文枢

一个轻量、快速的个人文本信息管理与多设备同步工具。

打开即用，发布即同步。在手机上随手记一条想法，电脑上立刻就能看到。

## 它能做什么

**快速捕获想法**  
打开网页，输入内容，回车发送。没有复杂的编辑器，没有多余的步骤。页面秒开，操作零延迟。

**多设备同步**  
在任何设备的浏览器里打开同一个地址，发布的内容立刻出现在所有设备上。手机上复制一段文字，电脑上直接粘贴——文枢就是你的跨设备剪贴板。

**智能标签**  
发布消息时自动识别内容并打标签：
- 包含百度网盘、夸克网盘、阿里云盘等链接 → 自动标记「网盘」
- 其他内容 → 自动标记「日记」

标签栏显示在列表顶部，点击即可按标签筛选。同一条消息可以拥有多个标签。

**链接识别**  
消息中的 URL 自动变为可点击的蓝色链接，网盘资源一键直达。

**消息管理**
- 一键复制消息内容
- ○/✓ 标记为已处理（已处理消息显示删除线，一目了然）
- ⋯ 菜单删除不需要的消息

**分页浏览**  
支持首页、尾页、页码跳转，大量消息也能流畅浏览。

**多用户**  
注册登录后，每个用户拥有独立的私人空间，互不干扰。

## 适用场景

- **碎片信息收集** — 脑海中闪过的灵感、看到的好文章、值得记住的一句话
- **网盘资源管理** — 自动识别网盘链接，集中管理你的各种下载资源
- **跨设备文本接力** — 在一台设备上复制，在另一台设备上粘贴，告别微信文件传输助手
- **轻量待办** — 发布任务，完成后标记已处理，简单直接
- **个人日记** — 随时随地记录生活碎碎念
- **阅读清单** — 收集想读的文章和链接，读完标记已处理

## 技术架构

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│   浏览器      │────▶│  Vercel Edge      │────▶│  PostgreSQL  │
│  (任意设备)   │◀────│  (Serverless API  │◀────│  (Neon DB)   │
│              │     │   + 静态前端)      │     │              │
└──────────────┘     └──────────────────┘     └──────────────┘
```

- **前端**：React + Vite + Tailwind CSS
- **后端**：FastAPI (Python) Serverless 函数
- **数据库**：PostgreSQL (Vercel Postgres / Neon)
- **部署**：Vercel（全球 CDN，毫秒级响应）
- **认证**：JWT Token

## 本地开发

```bash
# 后端
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000

# 前端
cd frontend
npm install
npm run dev
```

访问 http://localhost:3000

## 部署到 Vercel

1. Fork 或 clone 本仓库
2. 在 [Vercel](https://vercel.com) 导入项目
3. 创建 Vercel Postgres 数据库（Storage → Create → Postgres）
4. 关联数据库到项目（Connect Project）
5. 部署完成，数据库表自动创建

## 项目结构

```
txthub/
├── api/                # Vercel Serverless 后端
│   ├── index.py        # API 路由 (FastAPI + PostgreSQL)
│   └── requirements.txt
├── backend/            # 本地开发后端 (FastAPI + SQLite)
│   ├── main.py
│   └── requirements.txt
├── frontend/           # React 前端
│   ├── src/
│   │   ├── App.jsx     # 主界面
│   │   └── App.css
│   ├── index.html
│   └── vite.config.js
├── vercel.json         # Vercel 部署配置
├── package.json        # 构建脚本
├── start.sh            # 本地一键启动
└── README.md
```

## License

MIT
