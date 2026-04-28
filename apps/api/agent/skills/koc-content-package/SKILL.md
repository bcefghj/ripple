---
name: koc-content-package
description: 选题确定后,生成完整的多平台可发布内容包(标题×10/封面×5/多平台脚本/合规审查/发布策略)
when_to_use: 当 KOC 已经选定话题,需要把选题转化为可直接发布的完整内容时
allowed_tools:
  - generate_titles
  - generate_covers
  - generate_script
  - search_assets
  - check_compliance
  - suggest_publish_strategy
triggers:
  - 帮我写
  - 生成文案
  - 出内容
  - 完整方案
  - 发布
context_fork: true
---

# KOC Content Package Skill

## 输出结构(严格 JSON)

```json
{
  "creative_brief": {
    "topic": "选题",
    "persona": "目标受众",
    "tension": "为什么有人会看",
    "promised_value": "看完得到什么"
  },
  "platform_packages": {
    "channels": {
      "format": "30秒口播",
      "script": "...",
      "captions": "...",
      "tags": [...],
      "cover_text": "..."
    },
    "wechat_official": {
      "format": "深度长文 1500-3000字",
      "title": "...",
      "outline": [...],
      "full_text": "...",
      "header_image": "..."
    },
    "xhs": {
      "format": "图文 1主图+8副图",
      "main_title": "...",
      "subtitle": "...",
      "body": "...",
      "tags": [...]
    },
    "douyin": {
      "format": "15秒强冲击",
      "hook_3s": "...",
      "script": "...",
      "background_music": "[版权友好]"
    },
    "bilibili": {
      "format": "5-10分钟中视频",
      "title": "...",
      "outline": [...],
      "script": "..."
    },
    "weibo": {
      "format": "140字 + 图",
      "text": "..."
    }
  },
  "title_candidates": [
    {"text": "标题1", "formula": "数字+痛点", "platforms": ["xhs", "weibo"]},
    {"text": "标题2", "formula": "好奇缺口", "platforms": ["channels"]},
    ... (10 个候选)
  ],
  "cover_candidates": [
    {"description": "高对比红黑配色", "main_text": "3字关键词", "style": "强冲击"},
    ... (5 个候选)
  ],
  "asset_plan": {
    "images_needed": ["插图1场景", "插图2场景"],
    "image_sources": ["unsplash", "pexels", "midjourney 生成"],
    "videos_needed": [],
    "music": {"source": "YouTube Audio Library", "track": "..."},
    "fonts": ["思源黑体", "阿里普惠体"],
    "license_notes": ["所有素材均为商用授权"]
  },
  "compliance_review": {
    "ai_label_required": true,
    "ai_label_text": "本内容由 AI 辅助创作",
    "sensitive_keywords_check": "passed",
    "copyright_risk": "low",
    "regulatory_flags": [],
    "platform_specific_warnings": []
  },
  "experiments": {
    "title_ab_pairs": [
      ["标题1", "标题2", "对比维度: 数字 vs 否定"]
    ],
    "thumbnail_variants": [
      {"variant_a": "高对比", "variant_b": "温和", "test_metric": "CTR"}
    ],
    "publish_times_hypothesis": [
      {"platform": "xhs", "time": "明天 10:30", "rationale": "粉丝活跃高峰"}
    ]
  }
}
```

## 生成原则

### 标题(必须 10 个)
按公式分类标注,每条都要标注最适合的平台:
- 数字型: "5 个让粉底液持妆 12 小时的小技巧"
- 否定式: "千万不要这样涂粉底液"
- 反差: "从素颜翻车到精致出门只用 3 步"
- 时效: "2026 年最值得入手的 10 款粉底液"
- 痛点共鸣: "打工人都懂的脱妆痛"
- 好奇缺口: "为什么大牌粉底液一滴管就够?"
- 人设口吻: "作为 8 年彩妆师,我只推荐这 3 款"

### 封面(必须 5 个候选)
- 高对比版(红黑/黄黑)
- 温和版(粉色/裸色)
- 极简版(留白 + 大字)
- 人脸版(情绪夸张)
- 无脸版(产品特写)

每个版本必须:
- 主文字 ≤ 5 个词(移动端可读)
- 安全区留白(不被遮挡)
- 描边/阴影确保识别

### 文案要求
- 风格匹配 KOC 历史作品(从 USER.md 取风格卡片)
- 必须有"线下细节"(具体时间/地点/场景)避免 AI 味
- 句式长度抖动(短句+长句混合)
- 关键数字具体化("从 300ms 拖到 900ms" > "显著提升")

### 平台适配规则
- **视频号**: 强社交链路,设计"可转发理由",评论区互动设计
- **公众号**: 深度长文,首屏价值高,可加目录
- **小红书**: 首图 + 8 字标题 + 第一段必须吸睛,SEO 关键词自然埋入
- **抖音**: 黄金 3 秒钩子,15 秒高密度,反转必在 5-10 秒
- **B站**: 中长视频,开头问题链 + 中段信息密度
- **微博**: 一句观点 + 一张可转发图

## 合规自检

### 必须检查的项
1. AI 生成内容必须显式标识(《AI 生成合成内容标识办法》)
2. 医疗/健康类必须有"非专业建议"声明
3. 财经/投资类必须有"不构成建议"声明
4. 品牌方合作必须标注"广告"
5. 引用数据必须有来源

### 必须避免的
- 绝对化表述(最、第一、唯一)
- 未经验证的功效宣称
- 政治敏感
- 未成年保护边界
- 涉及他人隐私

## 发布策略

基于 Oracle Skill 的早期信号窗口给出建议:
- 高置信度信号(>0.7)且窗口 < 3 天: "立即发布"
- 中等置信度(0.4-0.7): "AB 测试小范围"
- 低置信度(<0.4): "作为长期内容储备"

发布时间建议:
- 视频号: 朋友圈活跃高峰(晚间 19-21 时)
- 抖音: 通勤(8-9, 17-19) + 睡前(21-23)
- 小红书: 早晨(7-9) + 午休(12-14) + 晚间(20-23)
- B站: 周末白天 + 工作日晚间
