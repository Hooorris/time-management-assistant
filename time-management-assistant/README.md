# Time Management Assistant

个人时间管理 AI Agent 工程。当前阶段已经完成 Agent 规范、FastAPI 后端、PostgreSQL 连接层、核心业务 API、Scheduler、本地 MCP Server，以及 LLM-assisted 本地 Agent CLI；后续会继续完善测试和通知通道。

## Status

Version: v1.0
Status: LLM Agent Parser Implemented
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
├── agent/
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

The backend currently provides FastAPI startup, configuration loading, a basic health check, and a PostgreSQL connection health check. It does not implement `/tasks/*` business APIs yet.

Create a virtual environment and install dependencies:

```bash
python3.10 -m venv .venv
. .venv/bin/activate
pip install -r time-management-assistant/backend/requirements.txt
```

Step 7 adds the official MCP SDK, so the project virtual environment now needs Python 3.10 or newer.

Copy the environment template:

```bash
cp time-management-assistant/backend/.env.example time-management-assistant/backend/.env
```

Set `DATABASE_URL` in `time-management-assistant/backend/.env`. For remote development, keep PostgreSQL private and open an SSH tunnel:

```bash
ssh -L 5432:127.0.0.1:5432 ubuntu@124.222.128.159
```

Then use a local tunnel database URL:

```text
postgresql+psycopg://time_assistant:<password>@127.0.0.1:5432/time_management_assistant
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

With the SSH tunnel and `.env` configured, verify database connectivity:

```bash
curl http://127.0.0.1:8000/health/db
```

Expected response:

```json
{
  "status": "ok",
  "database": "time_management_assistant"
}
```

## Scheduler

The scheduler is a standalone worker that scans due reminders and sends notifications. It supports Bark and cc-connect for personal push notifications. HTTP, MCP, and Agent `check_reminders` still keep the previous mock behavior and do not send real notifications.

Run a one-time scan:

```bash
SCHEDULER_RUN_ONCE=true python time-management-assistant/scheduler/worker.py
```

Run continuously:

```bash
python time-management-assistant/scheduler/worker.py
```

Configuration is read from environment variables or `time-management-assistant/backend/.env`:

```text
SCHEDULER_INTERVAL_SECONDS=60
SCHEDULER_CHANNELS=bark
SCHEDULER_RUN_ONCE=false
SCHEDULER_LOG_LEVEL=INFO
NOTIFICATION_ENABLED=false
NOTIFICATION_CHANNELS=bark
BARK_SERVER_URL=https://api.day.app
BARK_DEVICE_KEY=<your-bark-key>
BARK_SOUND=bell
BARK_GROUP=Time Management Assistant
CC_CONNECT_PROJECT=my-project
CC_CONNECT_COMMAND=cc-connect
CC_CONNECT_TIMEOUT_SECONDS=30
```

`NOTIFICATION_ENABLED=false` is the safe default. In this dry-run mode the worker does not make any real HTTP request or run `cc-connect`; due reminders are treated as successfully handled so local scans remain easy to test.

To send through Bark, set `NOTIFICATION_ENABLED=true`, `NOTIFICATION_CHANNELS=bark`, and `BARK_DEVICE_KEY` only on the machine that should actually push notifications.

To send through cc-connect, set `NOTIFICATION_ENABLED=true`, `NOTIFICATION_CHANNELS=wechat_work`, and `CC_CONNECT_PROJECT`. The database already supports the `wechat_work` reminder channel, and the worker maps that channel to `cc-connect send -p <project> -m <message>` without changing the database schema.

Keep `.env`, database passwords, Bark keys, and any cc-connect local credentials out of Git.

When notification sending succeeds, the worker sets `reminders.status=sent`, stores `sent_at`, and marks the related task as `reminded=true`. When sending fails, the worker sets `reminders.status=failed` with the error message and leaves the task unreminded. Reminders already marked `sent` or `failed` are not sent again.

For remote development, keep the PostgreSQL SSH tunnel open before starting the worker.

## Local Runtime Helpers

Keep local-only tunnel and database values in `time-management-assistant/backend/.env`; this file is ignored by Git. The helper below reads `SSH_TUNNEL_*` values from that file and does not require secrets in command arguments:

```bash
python time-management-assistant/scripts/db_tunnel.py start
python time-management-assistant/scripts/db_tunnel.py status
python time-management-assistant/scripts/db_tunnel.py stop
```

Use `start` before running tests, the API, MCP server, Agent CLI, or scheduler against the remote PostgreSQL database.

For unattended local running on macOS, install LaunchAgents for the database tunnel and scheduler:

```bash
python time-management-assistant/scripts/launchd.py install
python time-management-assistant/scripts/launchd.py status
python time-management-assistant/scripts/launchd.py uninstall
```

The generated LaunchAgent plists live in `~/Library/LaunchAgents`, and logs live in `~/Library/Logs/time-management-assistant`. The plists do not contain SSH, database, or Bark secrets; runtime secrets stay in the ignored `backend/.env`.

`install` starts the scheduler immediately. By default it requires `NOTIFICATION_ENABLED=true` so due reminders are not silently marked sent in dry-run mode. For deliberate dry-run daemon testing, pass `--allow-dry-run-scheduler`.

## MCP Server

The MCP server exposes the same task capabilities as local tools for Codex, Claude Desktop, Cursor, ChatGPT Agent, and other MCP clients. Step 7 uses local `stdio` transport only and does not implement HTTP or SSE transports yet.

Install dependencies:

```bash
. .venv/bin/activate
pip install -r time-management-assistant/backend/requirements.txt
```

Set local-only MCP configuration in `time-management-assistant/backend/.env`:

```text
MCP_AUTH_REQUIRED=true
MCP_AUTH_TOKEN=<local-mcp-token>
DATABASE_URL=postgresql+psycopg://time_assistant:<password>@127.0.0.1:5432/time_management_assistant
```

For remote development, keep the PostgreSQL SSH tunnel open, then start the server:

```bash
python time-management-assistant/mcp_server/server.py
```

Available MCP tools:

```text
create_task
update_task
delete_task
query_task
list_today_tasks
query_schedule
complete_task
set_recurring_task
daily_summary
check_reminders
```

`delete_task` must only be called after the Agent or client has already confirmed the destructive action with the user. `check_reminders` marks due reminders as sent with mock behavior and does not send real Telegram, Email, Bark, WeChat Work, or DingTalk notifications. Real notifications are only sent by the scheduler worker.

## Local Agent CLI

The local Agent CLI parses Chinese schedule commands, then calls the existing service layer. Step 9 adds an LLM-assisted parser with rule-parser fallback.

Run one command:

```bash
python time-management-assistant/agent/cli.py once "明天下午3点提醒我写周报"
```

Start interactive mode:

```bash
python time-management-assistant/agent/cli.py chat
```

Parser modes:

```bash
python time-management-assistant/agent/cli.py --parser auto once "明天下午3点提醒我写周报"
python time-management-assistant/agent/cli.py --parser rule once "明天下午3点提醒我写周报"
python time-management-assistant/agent/cli.py --parser llm once "明天下午3点提醒我写周报"
```

`auto` is the default. It uses the LLM parser when `OPENAI_API_KEY` is configured and falls back to the rule parser when the key is missing or parsing fails.

LLM configuration lives in `time-management-assistant/backend/.env`:

```text
AGENT_LLM_PROVIDER=openai
AGENT_LLM_MODEL=gpt-5-mini
AGENT_LLM_TIMEOUT_SECONDS=30
AGENT_LLM_TEMPERATURE=0
OPENAI_API_KEY=<your-openai-api-key>
```

Supported examples:

```text
明天下午3点提醒我写周报
今天有什么安排
把健身改到明天早上8点
取消周五下午会议
周报完成了
每天早上8点学习英语
每日总结
检查提醒
```

Delete commands are interactive: the CLI first shows the matched task and only deletes after you type `yes`.

The LLM parser only extracts structured intent and arguments. All database reads and writes still go through `TaskService`, and delete commands still require interactive confirmation.

## Tests

Step 10 adds automated tests for the parser, LLM parser, service layer, HTTP API, MCP tool registration, scheduler scan, and Agent runner.

Install test dependencies:

```bash
pip install -r time-management-assistant/backend/requirements.txt
```

Run static checks:

```bash
python -m py_compile $(find time-management-assistant/backend/app time-management-assistant/scheduler time-management-assistant/mcp_server time-management-assistant/agent time-management-assistant/notifications -name '*.py' -print)
```

Run tests:

```bash
pytest time-management-assistant/tests
```

Integration tests require `DATABASE_URL`. For remote development, keep the PostgreSQL SSH tunnel open before running pytest.
