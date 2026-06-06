# TxtHub

一个轻量的消息发布与管理服务，支持智能标签分类。

## 功能

- 发布消息，支持多行输入
- 每条消息可复制、标记已处理/撤销
- 自动智能标签：网盘链接自动归类，其余归为日记
- 标签筛选（带数量统计）
- 分页浏览（首页/尾页/页码跳转）
- 多用户注册登录

## 本地开发

```bash
# 安装后端依赖
cd backend && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 安装前端依赖
cd frontend && npm install

# 启动
./start.sh
```

访问 http://localhost:3000

## 部署到 Vercel

### 1. 准备数据库

在 Vercel Dashboard → Storage → Create Database → 选择 **Postgres**。

创建后会自动注入 `POSTGRES_URL` 环境变量。

### 2. 部署

```bash
npm i -g vercel
vercel
```

或在 Vercel Dashboard 中 Import 此 Git 仓库。

### 3. 环境变量

确保以下环境变量已设置（Vercel Postgres 会自动设置）：

- `POSTGRES_URL` — PostgreSQL 连接字符串

### 4. 初始化数据库

部署后访问一次任意页面，数据库表会自动创建。

## 项目结构

```
txthub/
├── api/              # Vercel Serverless 函数 (FastAPI + PostgreSQL)
│   ├── index.py      # 入口
│   ├── main.py       # API 路由
│   ├── database.py   # 数据库连接
│   └── requirements.txt
├── backend/          # 本地开发后端 (FastAPI + SQLite)
├── frontend/         # React 前端
├── vercel.json       # Vercel 部署配置
├── package.json      # 构建脚本
└── start.sh          # 本地启动脚本
```
