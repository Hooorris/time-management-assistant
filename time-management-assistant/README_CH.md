# 时间管理助手

个人时间管理 AI Agent 工程。当前阶段已经完成 Agent 规范、最小 FastAPI 后端骨架，以及 PostgreSQL 数据库连接层；后续会继续实现业务 API、Scheduler、MCP Server 和测试。

## 项目状态

版本：v1.0
状态：数据库连接层已完成
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
python3 -m venv .venv
. .venv/bin/activate
pip install -r time-management-assistant/backend/requirements.txt
```

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
