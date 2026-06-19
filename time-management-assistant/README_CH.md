# 时间管理助手

个人时间管理 AI Agent 工程。当前阶段已经完成 Agent 规范、FastAPI 后端、PostgreSQL 连接层、核心业务 API、Scheduler、本地 MCP Server，以及 LLM-assisted 本地 Agent CLI；后续会继续完善测试和通知通道。

## 项目状态

版本：v1.0
状态：LLM Agent Parser 已完成
负责人：hsx

## 项目目标

用户通过自然语言完成个人日程管理，包括创建任务、修改任务、删除任务、查询日程、到点提醒和每日总结。目标是让用户不需要打开日历，只通过聊天即可完成大部分时间管理。

## 目录结构

```text
time-management-assistant/
├── README.md
├── README_CH.md
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

## 推荐开发顺序

1. PRD
2. AGENTS
3. TOOLS
4. DATABASE
5. API
6. Backend
7. Scheduler
8. MCP
9. Agent

## V1 范围

支持：

- 创建任务
- 修改任务
- 删除任务前确认
- 查询日程
- 标记任务完成
- 设置重复任务元数据
- 检查提醒
- 生成每日总结

暂不支持：

- 多用户协作
- 日历共享
- AI 自动排期
- 自动冲突解决
- Google Calendar、Apple Calendar、Outlook 同步

## 默认技术栈

- Agent：GPT-5 / Codex / Claude 兼容工具调用
- 后端：FastAPI
- 数据库：PostgreSQL
- 调度器：每分钟提醒扫描
- API 风格：JSON over HTTP
- MCP：面向 Codex、Claude Desktop、Cursor、ChatGPT Agent 的工具桥接

## 后端快速启动

当前后端提供 FastAPI 启动、配置加载、基础健康检查，以及 PostgreSQL 连接健康检查。当前还没有实现 `/tasks/*` 业务接口。

创建虚拟环境并安装依赖：

```bash
python3.10 -m venv .venv
. .venv/bin/activate
pip install -r time-management-assistant/backend/requirements.txt
```

Step 7 引入了官方 MCP SDK，因此项目虚拟环境现在需要 Python 3.10 或更新版本。

复制环境变量模板：

```bash
cp time-management-assistant/backend/.env.example time-management-assistant/backend/.env
```

在 `time-management-assistant/backend/.env` 中设置 `DATABASE_URL`。远程开发时，推荐保持 PostgreSQL 不暴露公网，通过 SSH 隧道访问：

```bash
ssh -L 5432:127.0.0.1:5432 ubuntu@124.222.128.159
```

然后在本地使用隧道数据库连接：

```text
postgresql+psycopg://time_assistant:<password>@127.0.0.1:5432/time_management_assistant
```

启动 API：

```bash
uvicorn app.main:app --reload --app-dir time-management-assistant/backend
```

验证基础健康检查：

```bash
curl http://127.0.0.1:8000/health
```

预期返回：

```json
{
  "status": "ok",
  "service": "Time Management Assistant API",
  "environment": "development",
  "timezone": "Asia/Shanghai"
}
```

配置 SSH 隧道和 `.env` 后，验证数据库连接：

```bash
curl http://127.0.0.1:8000/health/db
```

预期返回：

```json
{
  "status": "ok",
  "database": "time_management_assistant"
}
```

## 当前远程数据库说明

远程 PostgreSQL 已安装在 Ubuntu 服务器上，并保持只监听服务器本机地址：

```text
127.0.0.1:5432
```

这意味着数据库没有直接暴露公网。开发时通过 SSH 隧道连接，后端仍然使用 `127.0.0.1:5432` 访问数据库。

已创建数据库表：

- `tasks`
- `operation_logs`
- `reminders`

## Scheduler

Scheduler 是独立运行的提醒扫描 worker，会定期查找已到期的 reminder，并调用现有 service 将 reminder 标记为 `sent`、将关联 task 标记为 `reminded=true`。

当前 Step 6 只做 mock 通知：到期提醒会输出到日志，不会真正发送 Telegram、Email 或 Bark。

执行一次扫描：

```bash
SCHEDULER_RUN_ONCE=true python time-management-assistant/scheduler/worker.py
```

持续运行：

```bash
python time-management-assistant/scheduler/worker.py
```

可配置环境变量：

```text
SCHEDULER_INTERVAL_SECONDS=60
SCHEDULER_CHANNELS=telegram
SCHEDULER_RUN_ONCE=false
SCHEDULER_LOG_LEVEL=INFO
```

远程开发时，运行 scheduler 前需要先保持 PostgreSQL SSH 隧道开启。

## MCP Server

MCP Server 会把现有任务能力暴露为本地工具，供 Codex、Claude Desktop、Cursor、ChatGPT Agent 和其他 MCP 客户端调用。Step 7 只实现本地 `stdio` transport，暂不实现 HTTP 或 SSE transport。

安装依赖：

```bash
. .venv/bin/activate
pip install -r time-management-assistant/backend/requirements.txt
```

在 `time-management-assistant/backend/.env` 中配置本地 MCP 访问参数：

```text
MCP_AUTH_REQUIRED=true
MCP_AUTH_TOKEN=<local-mcp-token>
DATABASE_URL=postgresql+psycopg://time_assistant:<password>@127.0.0.1:5432/time_management_assistant
```

远程开发时，先保持 PostgreSQL SSH 隧道开启，然后启动 MCP Server：

```bash
python time-management-assistant/mcp_server/server.py
```

已暴露 MCP tools：

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

`delete_task` 必须在 Agent 或客户端已经向用户确认删除后才能调用。`check_reminders` 当前只会把到期提醒标记为已发送，不会真正发送 Telegram、Email、Bark、企业微信或钉钉通知。

## 本地 Agent CLI

本地 Agent CLI 会解析中文日程指令，然后调用现有 service 层完成操作。Step 9 新增 LLM-assisted parser，并保留规则解析器作为 fallback。

执行单条指令：

```bash
python time-management-assistant/agent/cli.py once "明天下午3点提醒我写周报"
```

启动交互模式：

```bash
python time-management-assistant/agent/cli.py chat
```

解析模式：

```bash
python time-management-assistant/agent/cli.py --parser auto once "明天下午3点提醒我写周报"
python time-management-assistant/agent/cli.py --parser rule once "明天下午3点提醒我写周报"
python time-management-assistant/agent/cli.py --parser llm once "明天下午3点提醒我写周报"
```

`auto` 是默认模式。配置了 `OPENAI_API_KEY` 时优先使用 LLM parser；未配置 key 或 LLM 解析失败时自动回退到规则解析器。

LLM 配置写在 `time-management-assistant/backend/.env`：

```text
AGENT_LLM_PROVIDER=openai
AGENT_LLM_MODEL=gpt-5-mini
AGENT_LLM_TIMEOUT_SECONDS=30
AGENT_LLM_TEMPERATURE=0
OPENAI_API_KEY=<your-openai-api-key>
```

支持示例：

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

删除指令会进入交互确认：CLI 会先展示匹配任务，只有输入 `yes` 后才会删除。

LLM parser 只负责抽取结构化意图和参数。所有数据库读写仍然通过 `TaskService`，删除指令仍然必须交互确认。

## 测试

Step 10 新增自动化测试，覆盖规则解析器、LLM parser、service 层、HTTP API、MCP tools 注册、scheduler 扫描和 Agent runner。

安装测试依赖：

```bash
pip install -r time-management-assistant/backend/requirements.txt
```

运行静态检查：

```bash
python -m py_compile $(find time-management-assistant/backend/app time-management-assistant/scheduler time-management-assistant/mcp_server time-management-assistant/agent -name '*.py' -print)
```

运行测试：

```bash
pytest time-management-assistant/tests
```

集成测试需要配置 `DATABASE_URL`。远程开发时，运行 pytest 前需要先保持 PostgreSQL SSH 隧道开启。
