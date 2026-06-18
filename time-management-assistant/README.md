# Time Management Assistant

个人时间管理 AI Agent 工程规范。当前阶段只定义产品、Agent 规则、工具、数据库、HTTP API 和 MCP Server 契约，后续再基于这些规范生成 FastAPI 后端、Scheduler、MCP Server 和测试。

## Status

Version: v1.0
Status: Specification Draft
Owner: hsx

## Goal

用户通过自然语言完成个人日程管理，包括创建任务、修改任务、删除任务、查询日程、到点提醒和每日总结。用户不需要打开日历，只通过聊天即可完成大部分时间管理。

## Directory

```text
time-management-assistant/
├── README.md
├── PRD.md
├── AGENTS.md
├── SYSTEM_PROMPT.md
├── TOOLS.md
├── DATABASE_SCHEMA.sql
├── OPENAPI.yaml
├── MCP_SERVER_SPEC.md
├── docs/
├── backend/
├── scheduler/
├── mcp_server/
└── tests/
```

## Recommended Development Order

1. PRD
2. AGENTS
3. TOOLS
4. DATABASE
5. API
6. Backend
7. Scheduler
8. MCP
9. Agent

## V1 Scope

In scope:

- Create task
- Update task
- Delete task with confirmation
- Query schedule
- Complete task
- Set recurring task metadata
- Check reminders
- Generate daily summary

Out of scope:

- Multi-user collaboration
- Calendar sharing
- AI automatic scheduling
- Automatic conflict resolution
- Calendar provider sync

## Default Stack

- Agent: GPT-5 / Codex / Claude-compatible tool calling
- Backend: FastAPI
- Database: PostgreSQL
- Scheduler: one-minute reminder scanner
- API style: JSON over HTTP
- MCP: tool bridge for Codex, Claude Desktop, Cursor, and ChatGPT Agent
