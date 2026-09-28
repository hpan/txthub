# 文枢 · 前端

React + Vite + Tailwind CSS 构建的单页应用。

## 开发

```bash
npm install
npm run dev      # 启动开发服务器 (localhost:3000)
npm run build    # 构建生产版本 → dist/
```

开发模式下 `/api` 请求自动代理到后端 `http://127.0.0.1:8000`（见 `vite.config.js`）。

## 关键文件

| 文件 | 用途 |
|------|------|
| `src/App.jsx` | 全部 UI 逻辑：认证、消息列表、标签筛选、编辑、分页 |
| `src/index.css` | Tailwind 指令入口 |
| `public/sw.js` | Service Worker（缓存策略） |
| `public/manifest.json` | PWA 清单 |

## 技术栈

- **React 19** — UI 框架
- **Vite 5** — 构建工具
- **Tailwind CSS 3** — 样式
- **PWA** — Service Worker + manifest.json
