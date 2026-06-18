# MCP Server Spec

## Purpose

Expose the Time Management Assistant tools through an MCP server so Codex, Claude Desktop, Cursor, ChatGPT Agent, and other MCP clients can manage personal schedule data through stable tool contracts.

## Server

Name: `time-management-assistant`

Default transport for local development: stdio

Future transports:

- Streamable HTTP
- Server-sent events

## Shared Rules

- All tool input and output is JSON.
- All timestamps use ISO 8601.
- The server must authenticate access to personal task data.
- The server must not return fabricated task data.
- Write operations must record `operation_logs`.
- `delete_task` must only be called after user confirmation by the Agent.

## Tools

### create_task

Description: Create a new task or reminder.

Input schema:

```json
{
  "type": "object",
  "required": ["title"],
  "properties": {
    "user_command": { "type": "string" },
    "title": { "type": "string" },
    "description": { "type": ["string", "null"] },
    "start_time": { "type": ["string", "null"], "format": "date-time" },
    "end_time": { "type": ["string", "null"], "format": "date-time" },
    "priority": { "type": "string", "enum": ["low", "medium", "high"] },
    "reminder_time": { "type": ["string", "null"], "format": "date-time" },
    "recurring_rule": { "type": ["string", "null"] }
  }
}
```

Output: task object and `task_id`.

### update_task

Description: Update an existing task.

Input schema:

```json
{
  "type": "object",
  "required": ["task_id", "changes"],
  "properties": {
    "user_command": { "type": "string" },
    "task_id": { "type": "string", "format": "uuid" },
    "changes": { "type": "object" }
  }
}
```

Output: updated task and before snapshot.

### delete_task

Description: Delete an existing task after explicit user confirmation.

Input schema:

```json
{
  "type": "object",
  "required": ["task_id"],
  "properties": {
    "user_command": { "type": "string" },
    "task_id": { "type": "string", "format": "uuid" }
  }
}
```

Output: deleted task snapshot.

### query_task

Description: Find tasks by id, title query, status, local day, or time range.

Input schema:

```json
{
  "type": "object",
  "properties": {
    "task_id": { "type": ["string", "null"], "format": "uuid" },
    "query": { "type": ["string", "null"] },
    "date": { "type": ["string", "null"], "format": "date" },
    "start_time_from": { "type": ["string", "null"], "format": "date-time" },
    "start_time_to": { "type": ["string", "null"], "format": "date-time" },
    "status": { "type": ["string", "null"], "enum": ["pending", "done", "cancelled", null] },
    "limit": { "type": "integer", "default": 10 }
  }
}
```

Output: list of matching tasks.

### list_today_tasks

Description: List today's tasks in the user's local timezone. This is a convenience tool for common daily schedule queries.

Input schema:

```json
{
  "type": "object",
  "properties": {
    "timezone": { "type": "string", "default": "Asia/Shanghai" },
    "include_done": { "type": "boolean", "default": true }
  }
}
```

Output: list of today's tasks ordered by start time.

### query_schedule

Description: Query schedule by local date or explicit time range.

Input schema:

```json
{
  "type": "object",
  "properties": {
    "date": { "type": ["string", "null"], "format": "date" },
    "start_time_from": { "type": ["string", "null"], "format": "date-time" },
    "start_time_to": { "type": ["string", "null"], "format": "date-time" },
    "include_done": { "type": "boolean", "default": true },
    "timezone": { "type": "string", "default": "Asia/Shanghai" }
  }
}
```

Output: list of tasks ordered by start time.

### complete_task

Description: Mark a task as done.

Input schema:

```json
{
  "type": "object",
  "required": ["task_id"],
  "properties": {
    "user_command": { "type": "string" },
    "task_id": { "type": "string", "format": "uuid" }
  }
}
```

Output: updated task and before snapshot.

### set_recurring_task

Description: Create a new recurring task or attach recurrence metadata to an existing task.

Input schema:

```json
{
  "type": "object",
  "required": ["recurring_rule"],
  "properties": {
    "user_command": { "type": "string" },
    "task_id": { "type": ["string", "null"], "format": "uuid" },
    "title": { "type": ["string", "null"] },
    "start_time": { "type": ["string", "null"], "format": "date-time" },
    "recurring_rule": { "type": "string" },
    "reminder_time": { "type": ["string", "null"], "format": "date-time" }
  }
}
```

Output: created or updated task.

### daily_summary

Description: Generate a daily summary.

Input schema:

```json
{
  "type": "object",
  "properties": {
    "date": { "type": "string", "format": "date" },
    "timezone": { "type": "string", "default": "Asia/Shanghai" }
  }
}
```

Output: completed tasks, unfinished tasks, and completion rate.

### check_reminders

Description: Find and mark due reminders.

Input schema:

```json
{
  "type": "object",
  "properties": {
    "now": { "type": "string", "format": "date-time" },
    "channels": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["telegram", "email", "bark", "wechat_work", "dingtalk"]
      }
    }
  }
}
```

Output: due reminders and count.

## Backend Mapping

The MCP server should call the same service layer as the HTTP API:

- `create_task` -> `POST /tasks/create`
- `update_task` -> `POST /tasks/update`
- `delete_task` -> `POST /tasks/delete`
- `query_task` -> `GET /tasks/query`
- `list_today_tasks` -> `GET /tasks/query`
- `query_schedule` -> `GET /tasks/query`
- `complete_task` -> `POST /tasks/complete`
- `set_recurring_task` -> `POST /tasks/create` or `POST /tasks/update`
- `daily_summary` -> `POST /summary/daily`
- `check_reminders` -> `POST /reminder/check`
