#!/usr/bin/env node
/**
 * Ripple MCP Server
 *
 * 把 Ripple 的能力暴露为 MCP 工具,Cursor / Claude Code 可一键调用。
 *
 * 用法 (Cursor 配置 ~/.cursor/mcp.json):
 *   {
 *     "mcpServers": {
 *       "ripple": {
 *         "command": "npx",
 *         "args": ["-y", "@ripple/mcp"],
 *         "env": { "RIPPLE_API_BASE": "http://120.55.247.6" }
 *       }
 *     }
 *   }
 *
 * 暴露工具:
 *   - ripple_oracle_scan: 扫描 7 数据源
 *   - ripple_chat: 一句话调用完整 Orchestrator (流式)
 *   - ripple_persona_calibrate: 校准人设
 *   - ripple_persona_get: 获取人设向量
 *   - ripple_replay_get: 查看执行图
 *   - ripple_skills_list: 列出技能库
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const API_BASE = process.env.RIPPLE_API_BASE || "http://120.55.247.6";

const TOOLS = [
  {
    name: "ripple_chat",
    description:
      "Ripple 决策智能 OS 主入口:一句话输入,调度 7 层架构 + 10 大原创能力,流式输出可审决策。" +
      "适用场景:KOC 想知道发什么 / 怎么写 / 一周怎么规划 / 跨平台改写。",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "用户的一句话输入,例如 '我是美妆 KOC 这周该发什么'" },
        user_id: { type: "string", description: "用户 ID,默认 mcp_user" },
        session_id: { type: "string", description: "会话 ID,可选" },
      },
      required: ["query"],
    },
  },
  {
    name: "ripple_oracle_scan",
    description:
      "Oracle 早期信号雷达:并行扫描 7 个真实数据源 (Polymarket / Manifold / HackerNews / 微博 / 抖音 / 百度 / B 站)," +
      "返回各源 Top 10 热搜与 cross-platform 时差信号。零硬编码 Mock。",
    inputSchema: {
      type: "object",
      properties: {
        topic_seed: { type: "string", description: "(可选) 关键词种子,如 '黄金' / 'AI' / '美妆'" },
      },
    },
  },
  {
    name: "ripple_persona_calibrate",
    description:
      "用 5+ 历史样本校准 KOC 人设向量。生成 256 维 embedding + 10 维可解释指标 (formality / technicality / humor_density 等)。",
    inputSchema: {
      type: "object",
      properties: {
        user_id: { type: "string", description: "用户 ID" },
        samples: {
          type: "array",
          items: { type: "string" },
          description: "5-20 篇历史代表作",
        },
        branch: { type: "string", description: "分支名,默认 main", default: "main" },
      },
      required: ["user_id", "samples"],
    },
  },
  {
    name: "ripple_persona_get",
    description: "获取用户的人设向量 (10 维可解释指标 + 256 维 embedding 摘要)。",
    inputSchema: {
      type: "object",
      properties: {
        user_id: { type: "string", description: "用户 ID" },
        branch: { type: "string", default: "main" },
      },
      required: ["user_id"],
    },
  },
  {
    name: "ripple_replay_get",
    description:
      "获取一次执行的完整 Replay Graph (所有决策节点 + Merkle 链摘要 + 验证结果)。" +
      "用于回答 KOC 的 '为什么推荐这个' 类问题。",
    inputSchema: {
      type: "object",
      properties: {
        run_id: { type: "string", description: "运行 ID,从 ripple_chat 返回" },
      },
      required: ["run_id"],
    },
  },
  {
    name: "ripple_skills_list",
    description: "列出 Ripple Skill Library 中所有可用技能 (Markdown 加载,自进化)。",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "ripple_tools_list",
    description: "列出 Ripple Tool Registry 中所有可用工具及权限分级。",
    inputSchema: { type: "object", properties: {} },
  },
];

const server = new Server(
  { name: "ripple-mcp", version: "0.2.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "ripple_chat": {
        const resp = await fetch(`${API_BASE}/api/v2/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "Accept": "text/event-stream" },
          body: JSON.stringify({
            query: args.query,
            user_id: args.user_id || "mcp_user",
            session_id: args.session_id,
          }),
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

        // 收集 SSE 流到完整结果
        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        const events = [];
        let finalSummary = "";
        let runId = null;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          let idx;
          while ((idx = buffer.indexOf("\n\n")) >= 0) {
            const chunk = buffer.slice(0, idx).trim();
            buffer = buffer.slice(idx + 2);
            if (!chunk.startsWith("data:")) continue;
            try {
              const evt = JSON.parse(chunk.slice(5).trim());
              events.push(evt);
              if (evt.type === "report_card" && evt.card_type === "final_summary") {
                finalSummary = evt.data?.text || "";
              }
              if (evt.type === "done") {
                runId = evt.run_id;
              }
            } catch {}
          }
        }

        return {
          content: [
            {
              type: "text",
              text:
                `## Ripple 执行完毕\n` +
                `**Run ID**: \`${runId || "?"}\`\n` +
                `**事件总数**: ${events.length}\n\n` +
                `## 最终结论\n${finalSummary}\n\n` +
                `## 思考过程摘要\n` +
                events
                  .filter((e) => ["thinking", "agent_start", "agent_end"].includes(e.type))
                  .map((e) => `- [${e.type}] ${e.text || e.agent || ""}`)
                  .slice(0, 30)
                  .join("\n"),
            },
          ],
        };
      }

      case "ripple_oracle_scan": {
        const r = await fetch(`${API_BASE}/api/v2/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: args.topic_seed
              ? `扫描数据源,关注 ${args.topic_seed} 相关话题`
              : "扫描 7 数据源找早期信号",
            user_id: "mcp_user",
          }),
        });
        const text = await r.text();
        // 提取 oracle_scan 卡片
        const lines = text.split("\n").filter((l) => l.startsWith("data:"));
        let scanData = null;
        for (const line of lines) {
          try {
            const evt = JSON.parse(line.slice(5).trim());
            if (evt.type === "report_card" && evt.card_type === "oracle_scan") {
              scanData = evt.data;
              break;
            }
          } catch {}
        }
        return {
          content: [
            {
              type: "text",
              text: scanData
                ? `## Oracle 扫描结果\n${JSON.stringify(scanData, null, 2)}`
                : "未获取到扫描数据",
            },
          ],
        };
      }

      case "ripple_persona_calibrate": {
        const r = await fetch(`${API_BASE}/api/v2/persona/calibrate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(args),
        });
        const data = await r.json();
        return {
          content: [
            { type: "text", text: `## 人设校准完成\n${JSON.stringify(data, null, 2)}` },
          ],
        };
      }

      case "ripple_persona_get": {
        const r = await fetch(
          `${API_BASE}/api/v2/persona/${args.user_id}?branch=${args.branch || "main"}`
        );
        if (r.status === 404) {
          return { content: [{ type: "text", text: "尚未校准人设,请先调用 ripple_persona_calibrate" }] };
        }
        const data = await r.json();
        return {
          content: [
            { type: "text", text: `## 当前人设\n${JSON.stringify(data, null, 2)}` },
          ],
        };
      }

      case "ripple_replay_get": {
        const r = await fetch(`${API_BASE}/api/v2/replay/${args.run_id}`);
        const data = await r.json();
        return {
          content: [
            { type: "text", text: `## Replay Graph (${args.run_id})\n${JSON.stringify(data, null, 2)}` },
          ],
        };
      }

      case "ripple_skills_list": {
        const r = await fetch(`${API_BASE}/api/v2/skills`);
        const data = await r.json();
        return {
          content: [
            { type: "text", text: `## Skill Library (${data.count})\n${JSON.stringify(data.skills, null, 2)}` },
          ],
        };
      }

      case "ripple_tools_list": {
        const r = await fetch(`${API_BASE}/api/v2/tools`);
        const data = await r.json();
        return {
          content: [
            { type: "text", text: `## Tool Registry (${data.count})\n${JSON.stringify(data.tools, null, 2)}` },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    return {
      content: [{ type: "text", text: `Error: ${error.message}` }],
      isError: true,
    };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
console.error(`Ripple MCP Server running, API_BASE=${API_BASE}`);
