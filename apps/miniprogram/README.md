# Ripple 微信小程序

> 灵感捕捉入口 + 移动端轻量版

## 为什么必须有小程序

腾讯 PCG 大赛赛道适配性的关键:
- KOC 大量时间在微信内
- 视频号 / 公众号 / 朋友圈是天然入口
- 微信云开发与元器 Agent 原生集成

## V1 功能(8 天内)

### 1. 灵感捕捉(核心)

```javascript
// pages/inspiration/index.js
Page({
  data: {
    inspiration: '',
  },
  onSubmit() {
    wx.cloud.callFunction({
      name: 'addInspiration',
      data: { content: this.data.inspiration }
    });
  },
});
```

### 2. 早期信号订阅(每日推送)

```javascript
// 调用我们的 FastAPI 后端
const requestEarlySignal = async (category) => {
  return await wx.request({
    url: 'https://api.ripple.io/api/v1/oracle/scan',
    method: 'POST',
    data: { topic_seed: category, category }
  });
};
```

### 3. 元器 Agent 入口(对话式)

```javascript
// 直接绑定到我们在元器创建的 Agent
const ripperAgentURL = 'https://yuanqi.tencent.com/openapi/v1/agent/chat/completions';
```

## V2 功能

- 视频号挂载小程序(归因 wxFinderId)
- 公众号文章嵌入
- 微信支付(订阅 Pro)
- 模板消息推送

## 目录结构

```
miniprogram/
├── app.js
├── app.json
├── app.wxss
├── pages/
│   ├── index/             # 主页
│   ├── inspiration/       # 灵感捕捉
│   ├── signals/           # 早期信号
│   └── agent/             # Agent 对话
├── components/
└── cloudfunctions/        # 云函数
    ├── addInspiration/
    └── callRippleAPI/
```

## 微信开发者工具

1. 注册小程序 (https://mp.weixin.qq.com)
2. 下载微信开发者工具
3. 导入本目录
4. 开通云开发(免费额度足够 demo)
