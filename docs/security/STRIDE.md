# Ripple STRIDE 威胁建模

> 完整威胁地图 + OWASP LLM Top 10 v2 全覆盖
>
> 版本: 1.0 / 2026-04-28

## 一、威胁总览(STRIDE)

| STRIDE | 全称 | 我们的高危场景 |
|--------|------|----------------|
| **S** | Spoofing(欺骗) | 钓鱼登录、伪造 OAuth 回调 |
| **T** | Tampering(篡改) | 恶意修改 KOC 草稿、供应链投毒 |
| **R** | Repudiation(抵赖) | 用户否认发布过某内容 |
| **I** | Information Disclosure(信息泄露) | 草稿 / API Key / 风格画像泄露 |
| **D** | Denial of Service(拒绝服务) | 刷接口、耗尽 LLM 配额 |
| **E** | Elevation of Privilege(权限提升) | Prompt Injection 操控 Agent 越权 |

---

## 二、威胁详细分析

### S - Spoofing 欺骗

| 威胁 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|---------|
| 钓鱼登录页 | 中 | 高 | OIDC + PKCE,官方域名教育,2FA 强制 |
| 伪造 OAuth 回调 | 中 | 高 | state 参数验证,设备绑定 |
| API 接口冒充 | 低 | 中 | 服务端 JWT 签名,客户端校验 |
| AI 生成虚假身份 | 中 | 高 | 内容生成必须显式 AI 标识(法规要求) |

### T - Tampering 篡改

| 威胁 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|---------|
| 恶意修改用户草稿 | 低 | 高 | 数据签名,审计日志,版本控制 |
| 供应链 npm/pip 包投毒 | 中 | 高 | SBOM,Dependabot,签名校验 |
| 模型权重投毒 | 极低 | 极高 | 仅使用大厂官方 API,不下载未知权重 |
| 输出被中间人改写 | 低 | 中 | TLS 1.3,HSTS,证书 pinning(桌面端) |

### R - Repudiation 抵赖

| 威胁 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|---------|
| 用户否认发布 | 中 | 高 | 完整审计日志(用户 ID + 时间 + 内容 hash) |
| 用户否认授权 | 中 | 高 | OAuth 授权快照存档,带时间戳 |
| 系统行为否认 | 低 | 中 | 不可篡改日志(WORM 存储或 hash chain) |

### I - Information Disclosure 信息泄露

| 威胁 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|---------|
| 用户 API Key 泄露 | 高 | **极高** | **BYOK 本地 AES-256-GCM + Argon2id 加密**,绝不上传服务器 |
| 草稿 / 灵感泄露 | 中 | 高 | 数据库 RLS 强制 tenant_id,加密 at rest |
| 风格画像被偷窃 | 中 | 中 | 多租户隔离 + 访问审计 |
| 系统提示泄露 | 中 | 中 | 系统 prompt 与用户消息分层,不可拼接 |
| 日志中 PII 泄露 | 中 | 高 | 日志脱敏(身份证 / 手机号 / API Key 正则替换) |
| 跨租户向量检索泄露 | 中 | 极高 | pgvector 强制 tenant_id 过滤,集成测试 |

### D - Denial of Service 拒绝服务

| 威胁 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|---------|
| 刷 LLM 接口耗尽配额 | **高** | **高** | per-tenant rate limit,Redis 计数器,配额预警 |
| 大输入 Prompt 攻击 | 中 | 中 | 输入长度限制 + token 预算硬截断 |
| 仿真节点 DoS | 低 | 低 | num_nodes 上限,执行超时 |
| 文件上传 zip bomb | 中 | 中 | 文件大小限制 + 扫描 |

### E - Elevation of Privilege 权限提升

| 威胁 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|---------|
| Prompt Injection 越权 | **极高** | **极高** | 工具 allowlist,人机确认,Hook 链拦截 |
| Agent 调用未授权工具 | 中 | 高 | canUseTool 严格白名单,默认 fail-closed |
| Subagent 提升权限 | 中 | 高 | 子 Agent 不可降级父级权限,depth 上限 |
| 跨租户数据访问 | 中 | 极高 | RLS + JWT 严格校验 + 集成测试 |

---

## 三、OWASP LLM Top 10 v2 (2024-11) 对应措施

### LLM01 - Prompt Injection
**风险**: 用户/外部内容注入恶意指令操控 Agent
**我们的措施**:
- 输入分层:`system prompt` 永不与 `user content` 直接拼接
- delimiter 标记用户输入
- ForumDebateAgent 多 Agent 投票降低单点 inject 影响
- 第三方 prompt firewall(可选: Lakera Guard)
- 输出过滤:LLM 输出经过结构化校验

### LLM02 - Sensitive Information Disclosure
**风险**: LLM 输出泄露训练数据或上下文
**我们的措施**:
- 输出过滤:正则脱敏 PII
- 不向 LLM 传未脱敏的用户敏感数据
- 日志脱敏

### LLM03 - Supply Chain
**风险**: 依赖包/模型权重投毒
**我们的措施**:
- SBOM(`pip freeze` / `npm audit`)
- Dependabot 自动 PR 升级
- 仅使用大厂官方 API,不下载未知权重
- 签名校验(`pip --require-hashes`)

### LLM04 - Data and Model Poisoning
**风险**: 训练/微调数据被污染
**我们的措施**:
- 不微调用户数据(BYOK 本地化)
- 用户协议明确"不训练用户数据"
- 输入验证

### LLM05 - Improper Output Handling
**风险**: LLM 输出直接执行(SQL/Shell)
**我们的措施**:
- LLM 输出绝不直接 `eval` / `exec`
- markdown → HTML 必须 sanitize
- JSON 输出必须 schema 校验

### LLM06 - Excessive Agency
**风险**: Agent 拥有过多权限
**我们的措施**:
- 工具 allowlist
- 敏感操作(发布/支付/账号)需人机确认
- Hooks PreToolUse 拦截危险工具
- canUseTool 默认 fail-closed

### LLM07 - System Prompt Leakage
**风险**: 系统 Prompt 被诱导泄露
**我们的措施**:
- 系统 Prompt 不与用户消息拼接
- 检测"忽略上述指令"等越狱模式

### LLM08 - Vector and Embedding Weaknesses
**风险**: 向量库跨租户检索 / embedding 反演
**我们的措施**:
- pgvector 强制 tenant_id 过滤
- namespace 隔离
- 不存敏感原文,只存摘要

### LLM09 - Misinformation
**风险**: LLM 输出虚假信息
**我们的措施**:
- FactCheckerAgent 强制审查
- 关键路径 RAG 检索强制
- Confidence scoring 输出
- 用户协议:免责声明

### LLM10 - Unbounded Consumption
**风险**: API 配额被刷爆 / 账单爆炸
**我们的措施**:
- per-tenant 每日 token 预算
- LLM 调用熔断器
- 异常检测:用户突然 100x 用量自动暂停
- BYOK 用户用自己的 Key,不影响我们成本

---

## 四、合规对应

### 《人工智能生成合成内容标识办法》(2025-09-01 施行)

**强制要求**:
- 显式标识(可见水印 + 文字声明)
- 隐式标识(元数据 / 文件结构)
- 不得删除 / 篡改 / 隐匿标识

**Ripple 实现**:
- RiskReviewerAgent 检查 AI 标识
- 生图 API 自动添加水印
- 文档元数据标记
- 用户尝试删除标识时弹出提醒

### 《互联网信息服务深度合成管理规定》

**要求**:
- 服务提供者标识义务
- 算法备案(若面向公众)
- 安全评估

**Ripple 实现**:
- 我们调用混元(已备案)而非自训模型
- 学生赛阶段标注"校内 demo + 腾讯云备案底座"
- 商用前完成算法备案

### 《个人信息保护法》(PIPL)

**要求**:
- 最小必要
- 用户同意
- 删除权 / 访问权
- 数据驻留

**Ripple 实现**:
- 注册表单字段最少
- 用户协议明确告知
- 提供数据导出与删除接口
- 中国区数据不出境

---

## 五、安全控制清单(50+ 条)

### 身份与访问(10)
- [x] OIDC 短期 access token + refresh 轮换
- [x] RBAC: free / pro / enterprise / admin
- [x] 管理后台独立 IdP + MFA
- [x] 服务间 mTLS(Enterprise 版)
- [x] 密钥用环境变量 + Vault(生产)
- [ ] CI 用 OIDC 拉云资源(待 V2)
- [x] 依赖 SCA(Dependabot)
- [x] 容器非 root
- [ ] SBOM 每版本归档(待 V2)
- [ ] 渗透测试(待 V3)

### LLM 专属(12)
- [x] LLM01 输入分层 delimiter
- [x] LLM02 输出过滤 PII
- [x] LLM03 SBOM + Dependabot
- [x] LLM04 BYOK 不训练用户数据
- [x] LLM05 markdown → HTML sanitize
- [x] LLM06 工具 allowlist + 人机确认
- [x] LLM07 system prompt 不拼接 user
- [x] LLM08 tenant 强制过滤
- [x] LLM09 FactChecker + Confidence
- [x] LLM10 per-tenant 配额 + 熔断

### 数据(10)
- [x] TLS 1.3 全链路
- [x] PII 脱敏
- [x] 日志 scrub
- [x] PostgreSQL RLS
- [x] 备份加密
- [x] 中国区数据不出境
- [x] 删除权 API
- [x] 保留期自动化
- [ ] DPA 子处理商清单(待商务)
- [x] 密钥本地加密

### 合规(10)
- [x] AI 标识办法对应
- [x] 深度合成规定对应
- [x] PIPL 对应
- [x] UGC 举报流程
- [x] 内容审核队列
- [x] 未成年人保护
- [ ] 算法备案(商用前)
- [x] AIGC 水印
- [x] 用户协议
- [x] 隐私政策

### 运营(8)
- [ ] SOC 告警(待 V2)
- [x] 异常登录检测
- [x] Secrets 泄露扫描
- [x] 事故响应模板
- [x] RTO/RPO 定义
- [ ] 灾备演练(待 V2)
- [x] LLM egress allowlist
- [ ] 员工 MDM(团队规模化时)

---

## 六、应急响应

### 高危事件分级
- **P0**: 数据泄露 / 服务全网宕机
- **P1**: 账号被盗 / 大规模合规风险
- **P2**: 单租户问题 / 单 Agent 故障
- **P3**: 体验问题

### P0 流程
1. 0-15 分钟: 立即下线受影响功能
2. 15-60 分钟: 评估影响范围,通知用户
3. 1-24 小时: 修复 + 验证 + 灰度恢复
4. 24-72 小时: 复盘报告 + 监管报告(若涉及)

---

## 七、答辩话术

如评委问"安全做了什么":

1. **OWASP LLM Top 10 v2 全覆盖**(可逐条解释)
2. **STRIDE 威胁建模**(此文档可展示)
3. **多租户 RLS 强制**(代码可演示)
4. **BYOK 本地 AES-256-GCM**(架构图可演示)
5. **AI 生成内容显式标识**(响应国家法规)
6. **不训练用户数据**(用户协议明确)
7. **集成测试覆盖跨租户场景**(测试代码可展示)

> 学生赛阶段可诚实说:"目前是开发版,商用前会完成算法备案 + 第三方渗透测试 + SOC 2 路径"
