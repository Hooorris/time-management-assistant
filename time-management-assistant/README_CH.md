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

架构说明：[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

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

Scheduler 是独立运行的提醒扫描 worker，会定期查找已到期的 reminder，并发送通知。当前支持 Bark 和 cc-connect，用于个人设备真实推送。

HTTP、MCP 和 Agent 的 `check_reminders` 仍保持原来的 mock 行为，不会触发真实通知，避免聊天查询时误发提醒。真实通知只由 Scheduler worker 执行。

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

`NOTIFICATION_ENABLED=false` 是安全默认值。dry-run 模式不会发起真实 HTTP 请求，也不会执行 `cc-connect`，但会把到期 reminder 当作处理成功，方便本地调试。

如果使用 Bark，在真实推送机器上设置 `NOTIFICATION_ENABLED=true`、`NOTIFICATION_CHANNELS=bark`，并填写 `BARK_DEVICE_KEY`。

如果使用 cc-connect，设置 `NOTIFICATION_ENABLED=true`、`NOTIFICATION_CHANNELS=wechat_work` 和 `CC_CONNECT_PROJECT`。数据库已经支持 `wechat_work` reminder channel，worker 会把这个通道映射到 `cc-connect send -p <project> -m <message>`，不需要修改数据库 schema。

`.env`、数据库密码、Bark key 和 cc-connect 本地凭据只保存在本地，不能提交到 Git。

通知发送成功时，worker 会设置 `reminders.status=sent`、写入 `sent_at`，并把关联 task 标记为 `reminded=true`。发送失败时，worker 会设置 `reminders.status=failed` 和错误信息，关联 task 不会被标记为已提醒。已经是 `sent` 或 `failed` 的 reminder 不会重复发送。

远程开发时，运行 scheduler 前需要先保持 PostgreSQL SSH 隧道开启。

## 本地运行检查

使用 doctor 脚本检查 `.env`、数据库隧道、PostgreSQL 连接、通知配置、scheduler
可加载性和 launchd 服务状态。该脚本不会修改数据库，也不会发送通知。

```bash
python time-management-assistant/scripts/doctor.py
```

## 本地运行助手

本地隧道和数据库真实配置放在 `time-management-assistant/backend/.env`，该文件已被 Git 忽略。下面的助手脚本会读取 `.env` 中的 `SSH_TUNNEL_*` 配置，不需要把密钥写到命令参数里：

```bash
python time-management-assistant/scripts/db_tunnel.py start
python time-management-assistant/scripts/db_tunnel.py status
python time-management-assistant/scripts/db_tunnel.py stop
```

连接远程 PostgreSQL 跑测试、API、MCP Server、Agent CLI 或 Scheduler 前，先执行 `start`。

如果要在 macOS 本机无人值守运行，可以安装 LaunchAgent，分别保活数据库隧道和 Scheduler：

```bash
python time-management-assistant/scripts/launchd.py install
python time-management-assistant/scripts/launchd.py status
python time-management-assistant/scripts/launchd.py uninstall
```

生成的 plist 位于 `~/Library/LaunchAgents`，日志位于 `~/Library/Logs/time-management-assistant`。plist 不包含 SSH、数据库、Bark 或 cc-connect 密钥；运行时密钥仍只保存在已忽略的 `backend/.env`。

`install` 会立即启动 Scheduler。默认要求 `NOTIFICATION_ENABLED=true`，避免 dry-run 模式静默把到期提醒标记为已发送。如果是有意做 dry-run 守护测试，可以加 `--allow-dry-run-scheduler`。

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

`delete_task` 必须在 Agent 或客户端已经向用户确认删除后才能调用。`check_reminders` 只保留 mock 行为，把到期提醒标记为已发送，但不会真正发送 Telegram、Email、Bark、企业微信或钉钉通知。真实通知只由 Scheduler worker 发送。

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
python -m py_compile $(find time-management-assistant/backend/app time-management-assistant/scheduler time-management-assistant/mcp_server time-management-assistant/agent time-management-assistant/notifications -name '*.py' -print)
```

运行测试：

```bash
pytest time-management-assistant/tests
```

集成测试需要配置 `DATABASE_URL`。远程开发时，运行 pytest 前需要先保持 PostgreSQL SSH 隧道开启。
