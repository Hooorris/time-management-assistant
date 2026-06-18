# Time Management Assistant

个人时间管理 AI Agent 工程。当前阶段已经完成 Agent 规范，并初始化了最小 FastAPI 后端骨架；后续会继续实现数据库、业务 API、Scheduler、MCP Server 和测试。

## Status

Version: v1.0
Status: Backend Bootstrap
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
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── tools/
│   ├── .env.example
│   └── requirements.txt
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

## Backend Quick Start

Step 1 provides a minimal FastAPI application with a health check only. It does not connect to PostgreSQL yet and does not implement `/tasks/*` business APIs yet.

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r time-management-assistant/backend/requirements.txt
```

Run the API locally:

```bash
uvicorn app.main:app --reload --app-dir time-management-assistant/backend
```

Verify:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "Time Management Assistant API",
  "environment": "development",
  "timezone": "Asia/Shanghai"
}
```
