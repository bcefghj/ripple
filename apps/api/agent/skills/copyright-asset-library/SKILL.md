---
name: copyright-asset-library
description: 版权友好的素材资源清单 - 图片/视频/音乐/字体白名单 + 风险检测
when_to_use: 选择内容素材时,确保版权安全
allowed_tools:
  - reverse_image_search
  - copyright_check
triggers:
  - 素材
  - 版权
  - 配图
  - 配乐
  - 字体
context_fork: false
---

# Copyright-Friendly Asset Library

## 黄金原则

> **可下载 ≠ 可商用 ≠ 可登记商标**
> 
> 任何"免费素材"都要看 License 条款细节

## 一、图片素材

### 推荐站点(免费商用)

| 站点 | URL | 许可证要点 |
|------|-----|------------|
| Unsplash | https://unsplash.com | 免费下载,常见于商业用途;注意肖像权与商标 |
| Pexels | https://www.pexels.com/license/ | 免费使用;肖像/地标个案判断 |
| Pixabay | https://pixabay.com/service/terms/ | 注意"商标与形象"条款 |
| Pikwizard | https://pikwizard.com | 免费,商业可用 |
| Burst (Shopify) | https://burst.shopify.com | 完全免费 |
| Reshot | https://www.reshot.com | 商用免费,无需署名 |

### 收费图库(更高质量)

| 站点 | 备注 |
|------|------|
| Adobe Stock | 订阅制,质量高 |
| Shutterstock | 业内标杆 |
| 摄图网 | 国内,中国元素丰富 |
| 包图网 | 国内,设计模板多 |
| 图虫创意 | 国内,摄影作品多 |

### AI 生成图片

| 模型 | 商业可用性 | 备注 |
|------|------------|------|
| 腾讯混元生图 | ✓ 商用可 | 国内合规优先 |
| DALL-E 3 (OpenAI) | ✓ 商用可 | 注意 OpenAI 条款 |
| Flux Pro / Schnell | ✓ Schnell 商用可,Pro 看 license | 写实质量高 |
| SDXL | ✓ 自部署可 | 需自己部署或服务商 |
| Midjourney | ⚠ 看订阅档 | Pro 起可商用 |
| 通义万相 | ✓ 商用可 | 阿里云 |

## 二、视频素材(B-Roll)

| 站点 | 备注 |
|------|------|
| Pexels Videos | 免费商用 |
| Mixkit | 免费商用 |
| Coverr | 免费,需署名 |
| Videvo | 部分免费 |
| Pond5 | 收费,选择最全 |
| Storyblocks | 订阅制 |

## 三、音乐(版权友好)

### 海外免费音乐

| 站点 | 备注 |
|------|------|
| YouTube Audio Library | 完全免费,需在 YouTube 内使用 |
| Free Music Archive | 多数 CC 协议 |
| Bensound | 免费需署名,商用付费 |
| Incompetech (Kevin MacLeod) | CC BY 4.0,需署名 |
| Pixabay Music | 免费商用 |

### 海外订阅音乐

| 站点 | 备注 |
|------|------|
| Epidemic Sound | $15/月,品质极高 |
| Artlist | $16/月,影视友好 |
| Soundstripe | $16/月 |
| AudioJungle | 单曲购买 |

### 国内音乐

| 站点 | 备注 |
|------|------|
| 网易云创作者中心 | 部分免费,部分需购买 |
| 腾讯音乐人 | 注册成创作者后部分可用 |
| Tunesat (官方曲库) | 部分免费 |

### 关键警告

- **YouTube Audio Library 的音乐 ≠ 在抖音可用**(各平台有独立版权识别)
- **优先使用平台官方曲库**(抖音/视频号都有创作者音乐库)
- **AI 生成音乐**(如 Suno)商业用途看具体订阅版本

## 四、字体(免费商用)

### 推荐字体

| 字体 | 来源 | 许可 |
|------|------|------|
| 思源黑体 / 思源宋体 | Adobe + Google | SIL Open Font License |
| 思源等宽 | 同上 | SIL OFL |
| 阿里巴巴普惠体 | 阿里巴巴 | 免费商用(需登记) |
| 站酷字体系列(高端黑等) | 站酷 | 免费商用 |
| 庞门正道字体 | 庞门正道 | 免费商用 |
| 江城字体 | 江城 | 部分免费 |
| Source Han Mono | Adobe | 免费商用 |

### 必避免

- 微软雅黑(默认 Windows,商用需授权)
- 苹方(macOS 默认,商用受限)
- 方正字库(收费)
- 汉仪字库(收费)

## 五、版权风险检测

### 必查项

1. **反向图搜**:
   - TinEye: https://tineye.com
   - Google Images: https://images.google.com
   - Yandex Images: https://yandex.com/images/

2. **音乐版权**:
   - YouTube Studio 审核
   - 各平台上传时的版权识别

3. **文字相似度**:
   - 朱雀 AI 检测: https://matrix.tencent.com/ai-detect/
   - 学术查重(为内容创作者:平台内部相似度)

### 检测流程

```
素材准备 → 反向图搜 → 音乐识别 → 文字查重 → 通过 → 使用
                    ↓ 失败
                    重新生成或更换
```

## 六、特殊场景

### 含人物肖像的素材
即使是 CC0 也要核查:
- 是否有 model release(模特同意书)
- 是否会用于"暗示该人代言"
- 商业广告必须有明确肖像授权

### 地标建筑摄影
某些国家(法国/意大利)的特定建筑商业拍摄受限:
- 巴黎埃菲尔铁塔夜景商业用途受限
- 罗马斗兽场商业用途需许可

### 奢侈品外观
- 出现 LV/Gucci/Hermes 等品牌 logo 商业用途风险高
- 替代:模糊化处理或选择 generic 替代品

### 未成年人
- 未经监护人同意不得使用未成年人形象
- AI 生成的未成年人形象也受限

## 七、合规叙事(评委友好)

在 PDF / 答辩时强调:
- 我们调用 Unsplash/Pexels/Pixabay 等已商用授权图库
- 字体使用思源/阿里普惠等免费商用字体
- 音乐优先平台原生曲库
- AI 生成内容显式标识(《AI 生成合成内容标识办法》)
- 反向图搜防止抄袭
- 提供版权检测 API,KOC 一键自检
