# @ripple/mcp

Ripple KOC 决策智能 OS 的 MCP Server。让你在 Cursor / Claude Code / 任何支持 MCP 的工具里直接调用 Ripple 的 7 层架构 + 10 大原创能力。

## 安装

无需安装 — 用 `npx` 直接运行:

```bash
npx -y @ripple/mcp
```

## 配置 (Cursor)

编辑 `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "ripple": {
      "command": "npx",
      "args": ["-y", "@ripple/mcp"],
      "env": {
        "RIPPLE_API_BASE": "http://120.55.247.6"
      }
    }
  }
}
```

## 配置 (Claude Code)

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ripple": {
      "command": "npx",
      "args": ["-y", "@ripple/mcp"]
    }
  }
}
```

## 暴露的工具

| 工具 | 说明 |
|------|------|
| `ripple_chat` | 一句话调用完整 Orchestrator (流式) |
| `ripple_oracle_scan` | Oracle 早期信号雷达 (7 数据源) |
| `ripple_persona_calibrate` | 人设向量校准 |
| `ripple_persona_get` | 获取当前人设 |
| `ripple_replay_get` | 查看决策 Replay Graph |
| `ripple_skills_list` | 列出 Skill Library |
| `ripple_tools_list` | 列出 Tool Registry |

## 自部署

把 `RIPPLE_API_BASE` 指向你自己的 Ripple FastAPI 服务即可 (默认指向官方 Demo)。

## License

Apache 2.0 © 戴尚好 (bcefghj@163.com)
