# FlowGuard · pitch-site

> 给 2026 飞书 AI 校园挑战赛评委看的项目介绍页。
> 两套风格 · 同一份内容 · 已部署到阿里云。

## 在线访问

| 入口 | 地址 |
| --- | --- |
| 主入口（双版本选择） | http://118.178.242.26/ |
| A 版 · 极简留白叙事派 | http://118.178.242.26/version-a-editorial/ |
| B 版 · 暗色科技 Agent OS | http://118.178.242.26/version-b-agent/ |
| Live Dashboard（v3） | http://118.178.242.26/dashboard |
| MCP HTTP API | http://118.178.242.26/mcp/tools |

## 目录结构

```
pitch-site/
├── README.md                       # 本文件
├── index.html                      # 主入口选择页（暗色科技风）
├── shared/                         # A/B 共用资源
│   ├── data.js                     # 单一数据源（所有文案、团队、功能清单）
│   ├── icons.js                    # SVG icon 集
│   ├── chat-simulator.js           # Demo 1 · 飞书聊天模拟器
│   ├── classifier-playground.js    # Demo 2 · 6 维分类试玩
│   ├── mcp-playground.js           # Demo 4 · MCP 在线调用
│   └── screenshots.js              # Demo 3 · 6 张飞书 UI mock 渲染
├── version-a-editorial/            # A 版 · Jane Li / Vercel / Resend 风
│   ├── index.html
│   ├── style.css
│   └── app.js
├── version-b-agent/                # B 版 · Linear / Anthropic Claude Code 风
│   ├── index.html
│   ├── style.css
│   └── app.js
└── deploy/
    ├── deploy_pitch.sh             # 一键部署 expect+scp
    └── nginx_pitch.conf            # nginx 路由
```

## 14 屏内容章节

1. **Hero** · 主标题 · 4 个关键数字
2. **Problem** · Mark 2005 学术引用 + 团队反思引文
3. **Solution** · 4 大支柱（Smart Shield / Context Recall / FlowMemory / MCP）
4. **Smart Shield** · 4 个 P 级卡片
5. **Demo 1 · 飞书聊天模拟器** ⭐ 90 秒自动播放
6. **Demo 2 · 6 维分类试玩** ⭐ 实时雷达图
7. **Demo 3 · 截图画廊** · 6 张飞书 UI 高保真 mock
8. **Killer Feature** · 4 步飞书工作台流程
9. **Inside the Engine** · 7 层架构 + 4 条 Claude Code 借鉴源
10. **Demo 4 · MCP 在线调用** ⭐ 真·live API
11. **Security · Trust** · 8 道闸门 + 6 项隐私承诺
12. **Honest Status** · Built / Lab / Planned 严格三列
13. **Tracks** · 三志愿 + 9 个飞书 API 标签云
14. **Team** · 戴尚号（USTC）+ 李洁盈（港科 TIE 全奖）
15. **Resources** · GitHub / PDF / Dashboard / 官方报名页
16. **FAQ** · 5 个常见问题

## 修改文案

所有文案集中在 `shared/data.js` 一份，A/B 两版同步生效。

## 部署到阿里云

```bash
cd pitch-site
bash deploy/deploy_pitch.sh
```

需要本机有 `expect`（Mac: `brew install expect`）。脚本会：
1. 打 tar 包
2. scp 上传到 `/tmp/`
3. ssh 远端解压到 `/var/www/pitch/`
4. 替换 `/etc/nginx/sites-enabled/flowguard_v3`
5. `nginx -t && systemctl reload nginx`
6. 公网 8 个 endpoint curl 验证

可重复执行（幂等）。旧的 nginx 配置会备份到服务器 `/root/nginx_backups/`。

## 本地预览

```bash
cd pitch-site
python3 -m http.server 8765
# 浏览器开 http://localhost:8765
```

## 技术栈

- HTML / CSS / JS only · 无构建、无 npm
- 字体 · Google Fonts CDN（Inter + JetBrains Mono）
- 共享 · 4 个 demo 模块都通过 `window.FG.*` 暴露
- 可访问 · 桌面 / 平板 / 手机均自适应

## 团队

- **戴尚号** · 中国科学技术大学硕士在读 · 全栈 / 工程 · [bcefghj.github.io](https://bcefghj.github.io/)
- **李洁盈 (Jane Li)** · 港科 TIE 全奖（2026 Incoming）· 产品 / 设计 · [janeliii.netlify.app](https://janeliii.netlify.app/)

MIT License · 2026
