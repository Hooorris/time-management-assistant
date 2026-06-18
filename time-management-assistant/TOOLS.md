# Tool Definitions

All tool inputs and outputs are JSON. All timestamps use ISO 8601 with timezone offset when available.

## Shared Types

### Task

```json
{
  "id": "uuid",
  "title": "写周报",
  "description": "",
  "start_time": "2026-06-19T15:00:00+08:00",
  "end_time": null,
  "priority": "medium",
  "status": "pending",
  "reminder_time": "2026-06-19T15:00:00+08:00",
  "recurring_rule": null,
  "reminded": false,
  "created_at": "2026-06-18T20:00:00+08:00",
  "updated_at": "2026-06-18T20:00:00+08:00"
}
```

### Error

```json
{
  "error": {
    "code": "ambiguous_task",
    "message": "Multiple matching tasks found."
  }
}
```

## create_task

Create a new task.

Input:

```json
{
  "user_command": "明天下午3点提醒我写周报",
  "title": "写周报",
  "description": "",
  "start_time": "2026-06-19T15:00:00+08:00",
  "end_time": null,
  "priority": "medium",
  "reminder_time": "2026-06-19T15:00:00+08:00",
  "recurring_rule": null
}
```

Output:

```json
{
  "task_id": "uuid",
  "task": {}
}
```

## update_task

Update an existing task. The Agent must query first unless `task_id` is already known from immediate context.

Input:

```json
{
  "user_command": "把健身改到明天早上8点",
  "task_id": "uuid",
  "changes": {
    "start_time": "2026-06-19T08:00:00+08:00",
    "reminder_time": "2026-06-19T08:00:00+08:00"
  }
}
```

Output:

```json
{
  "task": {},
  "before": {}
}
```

## delete_task

Delete an existing task. The Agent must confirm with the user before calling this tool.

Input:

```json
{
  "user_command": "取消周五下午会议",
  "task_id": "uuid"
}
```

Output:

```json
{
  "deleted_task": {}
}
```

## query_task

Find tasks by id, title query, status, day, or time range.

Input:

```json
{
  "task_id": null,
  "query": "健身",
  "date": "2026-06-19",
  "start_time_from": null,
  "start_time_to": null,
  "status": "pending",
  "limit": 10
}
```

Output:

```json
{
  "tasks": []
}
```

## list_today_tasks

List today's tasks in local timezone. This is a convenience wrapper around `query_schedule`.

Input:

```json
{
  "timezone": "Asia/Shanghai",
  "include_done": true
}
```

Output:

```json
{
  "tasks": []
}
```

## query_schedule

Query schedule by local date or time range.

Input:

```json
{
  "date": "2026-06-19",
  "start_time_from": null,
  "start_time_to": null,
  "include_done": true,
  "timezone": "Asia/Shanghai"
}
```

Output:

```json
{
  "tasks": []
}
```

## complete_task

Mark a task as done.

Input:

```json
{
  "user_command": "周报完成了",
  "task_id": "uuid"
}
```

Output:

```json
{
  "task": {},
  "before": {}
}
```

## set_recurring_task

Create or update recurrence metadata for a task.

Input:

```json
{
  "user_command": "每天早上8点学习英语",
  "task_id": null,
  "title": "学习英语",
  "start_time": "2026-06-19T08:00:00+08:00",
  "recurring_rule": "FREQ=DAILY;INTERVAL=1",
  "reminder_time": "2026-06-19T08:00:00+08:00"
}
```

Output:

```json
{
  "task": {}
}
```

## check_reminders

Find and mark due reminders.

Input:

```json
{
  "now": "2026-06-19T15:00:00+08:00",
  "channels": ["telegram"]
}
```

Output:

```json
{
  "reminders": [],
  "count": 0
}
```

## daily_summary

Generate a daily task summary.

Input:

```json
{
  "date": "2026-06-19",
  "timezone": "Asia/Shanghai"
}
```

Output:

```json
{
  "completed": [],
  "unfinished": [],
  "completion_rate": 67
}
```
