# Ripple 最终提交清单与命名规范

> 腾讯 PCG 校园 AI 产品创意大赛 · 命题 5
> 本文是参赛者提交前的「最后一公里」操作手册。

---

## 1. 提交内容总览(三件套)

| 类型 | 文件名 | 大小要求 | 内容 | 状态 |
|------|--------|----------|------|------|
| **Demo** | 在线链接 / 录制视频 | - | 可演示的产品 | ✅ |
| **录屏视频** | `选手姓名_命题5_Ripple_Demo演示.mp4` | ≤500MB | 3 分钟产品演示 | ⏳ 录制 |
| **PDF 文档** | `选手姓名_命题5_Ripple_Demo演示.pdf` | ≤50MB | 24 页提案 | ✅ 24 页 / 500KB |

**命名规则**(必须严格遵守):
```
选手姓名_命题5_Ripple_Demo演示.{pdf,mp4}
```

例如:`张三_命题5_Ripple_Demo演示.pdf`、`张三_命题5_Ripple_Demo演示.mp4`

---

## 2. Demo 链接(三选一,优先级从高到低)

### 优先级 1:本地 Docker 一键启动
```bash
git clone https://github.com/<your-handle>/ripple.git
cd ripple
./start.sh                                # 启动全部服务
# 或
docker compose -f infra/docker/docker-compose.yml up
```

### 优先级 2:云端在线 Demo
- 主链路:<https://ripple-demo.streamlit.app>(Streamlit Cloud)
- 备链路:<https://ripple.vercel.app>(产品介绍页 / Next.js)
- API 后端:<https://ripple-api-production.up.railway.app/docs>(Swagger)

### 优先级 3:录屏 + GitHub 源码(灾备)
- 录屏:`选手姓名_命题5_Ripple_Demo演示.mp4`
- 源码:<https://github.com/<your-handle>/ripple>

---

## 3. 文件准备清单(逐项确认)

### 3.1 PDF 文档(必交)
- [ ] 编译产物 `docs/proposal/main.pdf` 已生成
- [ ] 已重命名为 `选手姓名_命题5_Ripple_Demo演示.pdf`
- [ ] 文件大小 ≤ 50MB(当前 ~500KB,远低于上限)
- [ ] 封面 `[选手姓名]` `[学校]` `Demo 链接` 已替换为真实信息
- [ ] PDF 元信息(作者 / 标题)正确(用 Preview / Adobe Reader 验证)
- [ ] 在 Mac / Windows 至少 2 端打开预览,字体显示正常
- [ ] 备份 3 份:本地 + 飞书云盘 + GitHub Release

### 3.2 录屏视频(必交)
- [ ] 时长 ≤ 180 秒
- [ ] 文件大小 ≤ 500MB
- [ ] 1080p 30fps H.264 + AAC
- [ ] 已重命名为 `选手姓名_命题5_Ripple_Demo演示.mp4`
- [ ] 全程口播 / AI 配音清晰
- [ ] 全程硬字幕(白底黑字 ≥36px)
- [ ] 无未授权音乐 / 竞品 logo
- [ ] 备份 3 份:本地 + B 站(unlisted)+ 腾讯微云

### 3.3 Demo(必交)
- [ ] 本地一键启动可用 `./start.sh`
- [ ] 全部测试通过 `./start.sh test` (10 smoke + 10 E2E)
- [ ] BYOK 模式可用(无需服务器 Key)
- [ ] Mock 模式可用(完全离线)
- [ ] 至少 1 个云端备份在线(Streamlit Cloud / Railway / Vercel)
- [ ] 健康检查 ping 已配 UptimeRobot

### 3.4 源码(可选,加分项)
- [ ] GitHub 仓库公开
- [ ] README.md 完整
- [ ] LICENSE 文件(推荐 Apache 2.0 / MIT)
- [ ] CONTRIBUTING.md(可选)
- [ ] 使用 Releases 打 v1.0.0-submission 标签

---

## 4. 提交动作(执行顺序)

### Step 1:最终编译(D-1 21:00)
```bash
cd ripple
./start.sh test                # 跑全部测试,确认 20/20 通过
cd docs/proposal
./build.sh                     # 编译 PDF
mv main.pdf 张三_命题5_Ripple_Demo演示.pdf
```

### Step 2:录屏(D-1 22:00)
按 `docs/video/SCRIPT.md` 录制 3 分钟视频,导出为
`张三_命题5_Ripple_Demo演示.mp4`

### Step 3:多端备份(D-1 23:00)
```bash
# 命令行示例
TARGET_DIR=~/Desktop/Ripple_最终提交
mkdir -p $TARGET_DIR
cp 张三_命题5_Ripple_Demo演示.pdf $TARGET_DIR/
cp 张三_命题5_Ripple_Demo演示.mp4 $TARGET_DIR/

# 上传到至少 3 个位置
# 1. 本地外置硬盘
# 2. 飞书云盘 / 腾讯微云
# 3. GitHub Release
```

### Step 4:提交(D-Day)
1. 登录大赛指定提交平台
2. 上传 PDF + MP4(注意命名规范)
3. 填写 Demo 链接(用云端备份 URL)
4. 填写选手信息 / 学校 / 联系方式
5. 提交 → **截屏保存提交成功页面**!

### Step 5:监控(D-Day 至评审结束)
- UptimeRobot 监控 Demo URL,确保评审期不挂
- 关注大赛通知(邮箱 / 短信)
- 准备答辩(参考 `docs/defense/QA.md`)

---

## 5. 文件路径速查

| 文件 | 路径 | 用途 |
|------|------|------|
| PDF 提案 | `ripple/docs/proposal/main.pdf` | 主提交 |
| 录屏脚本 | `ripple/docs/video/SCRIPT.md` | 录屏指引 |
| 一键启动 | `ripple/start.sh` | Demo 启动 |
| 部署文档 | `ripple/docs/deployment/QUICKSTART.md` | 评委使用指南 |
| 云部署 | `ripple/docs/deployment/CLOUD_DEPLOY.md` | 云端备份 |
| 答辩 Q&A | `ripple/docs/defense/QA.md` | 答辩准备 |
| 五视角 review | `ripple/docs/review/CRITICAL_REVIEW.md` | 自检清单 |
| 安全文档 | `ripple/docs/security/STRIDE.md` | 合规材料 |
| BYOK 架构 | `ripple/docs/architecture/BYOK.md` | 技术补充 |

---

## 6. 提交后清单

- [ ] 截图保存提交成功页面
- [ ] 邮件给自己一份 PDF + MP4 备份
- [ ] 在飞书 / Notion 创建一份"已提交"记录
- [ ] 检查云端 Demo URL 仍在线
- [ ] 准备答辩(参考 docs/defense/QA.md)
- [ ] 通知导师 / 队友 / 推荐人

---

## 7. 答辩准备(若入围)

### 5 分钟答辩稿

**结构**:
1. **30 秒**:产品定位(KOC 的 Bloomberg Terminal)
2. **2 分钟**:Demo 现场演示(早期信号 + 12 Agent)
3. **1 分钟**:技术亮点(Claude Code 移植 + BYOK)
4. **1.5 分钟**:商业化路径(订阅 + 撮合 + 私有化)

### Q&A 高频问题

参考 `docs/defense/QA.md`,涵盖:
- 差异化 / 技术 / 商业模式 / 用户洞察 / 合规安全 五大类共 20 题

### 装备清单
- 笔记本(主) + 笔记本(备)
- HDMI / Type-C / Lightning 转接头各 1 个
- 两份 PDF(纸质 + 数字)
- Demo URL 写在便签上(防忘记)
- 充电器 + 充电宝
- 演讲稿(纸质 A4 大字版)
- 矿泉水 / 喉宝

---

## 8. 投票动员(若需要)

如果赛题包含网络投票环节:
- [ ] 提前准备 1 张分享卡片(微信好看 + 朋友圈封面)
- [ ] 同学群 / 校友群 / 老师群 推送
- [ ] 微博 / 小红书 发布作品介绍
- [ ] 拒绝刷票!保持公平竞争。

---

## 9. 应急预案

| 场景 | 预案 |
|------|------|
| 提交平台挂了 | 立刻邮件给主办方,附上 PDF + MP4 |
| Demo URL 挂了 | 切到本地启动 + 录屏播放 |
| 评委说"看不清" | 准备 720p 副本 / 高清原文件 |
| 评委要源码 | 提供 GitHub Release zip |
| 答辩当场卡顿 | 切到 PDF + 解说 |
| 答辩超时 | 严格压缩,优先讲早期信号杀手锏 |

---

## 10. 心态建议

> **做到 80% + 提交,胜过做到 100% + 错过截止**

- D-2 之前:打磨细节
- D-1:停手,只做备份与演练
- D-Day 上午:提交
- D-Day 下午:庆祝(或继续准备答辩)

**不要在最后一刻做大改动!** 小调整可能引入新 bug。

---

祝顺利夺奖!如有问题随时联系参赛者本人或翻阅本仓库其他文档。
