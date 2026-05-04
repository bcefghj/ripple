# LarkMentor 网页建设完整文档

> 本文件夹记录了 LarkMentor 官方网页从 0 到上线的完整过程：
> 设计思路 / 代码实现 / 后端改造 / 服务器部署 / 踩坑记录。
>
> 线上地址：http://118.178.242.26/
> 写于：2026-04-19

---

## 文件夹结构

```
website_build_doc/
├── README.md                   ← 本文件（总览导读）
├── 01_设计思路.md              ← 产品定位 + 页面设计决策
├── 02_前端实现.md              ← HTML / CSS / JS 技术细节
├── 03_后端改造.md              ← Dashboard + MCP Server 改造
├── 04_部署流程.md              ← 服务器部署 step-by-step
├── 05_踩坑记录.md              ← 7 个真实踩过的坑
└── code_snapshots/             ← 完整代码快照
    ├── index.html              ← 主页 HTML
    ├── style.css               ← 主页 CSS
    ├── app.js                  ← 主页 JS（数据+渲染+动画）
    ├── dashboard_v3.html       ← 新版 Dashboard HTML
    ├── mcp_server.py           ← 改造后的 MCP Server
    ├── deploy_lark_mentor.sh   ← 一键部署脚本
    ├── smoke_test.sh           ← 22 条验证断言
    └── nginx_larkmentor.conf   ← nginx server 配置
```

---

## 网页上线后的入口地址

| 入口 | URL | 说明 |
|---|---|---|
| 主页 | http://118.178.242.26/ | LarkMentor 产品介绍，14 章节 + 全动画 |
| Dashboard | http://118.178.242.26/dashboard | 周报 / Wrapped / 团队 / 安全审计 |
| MCP 可视化 | http://118.178.242.26/mcp | 14 工具卡片，可在线 call 真实后端 |
| MCP Raw JSON | http://118.178.242.26/mcp/tools | 给 Cursor / Claude Code 用的 JSON |
| MCP 别名 | http://118.178.242.26/mcp/tools.json | 同上 |
| 健康检查 | http://118.178.242.26/health | `{"status":"ok"}` |
| 技术报告 PDF | http://118.178.242.26/larkmentor_report.pdf | 下载 1.2MB PDF |

---

## 一句话总结各文档

- **01_设计思路**：为什么不用框架、为什么 14 个章节这样排序、用什么色系
- **02_前端实现**：IM 模拟器实现原理、6 维打分器、Typewriter 动画、FlowMemory 动画
- **03_后端改造**：Dashboard 新 API 对接 + demo fallback、MCP Server 新增可视化页
- **04_部署流程**：完整 SSH 命令流程、nginx 配置、systemd 配置、原子切换方法
- **05_踩坑记录**：gzip 导致 smoke 失败、reveal 对动态 DOM 无效等 7 个实际踩过的坑
