# PRD: Time Management Assistant

Version: v1.0
Author: hsx
Status: Draft

## 1. Product Overview

The Time Management Assistant is a personal AI Agent for schedule management. Users send natural-language commands, and the system interprets intent, reads or updates a Postgres database, sends reminders, and generates daily summaries.

The product is designed as an Agent-ready engineering project so Codex, Claude Code, OpenAI Agent, or another coding agent can generate implementation code from stable specs.

## 2. Product Goal

Let users manage personal time through chat instead of opening a calendar app.

V1 goals:

- Create tasks from natural language.
- Update and reschedule existing tasks.
- Delete tasks only after confirmation.
- Query schedules by day or time range.
- Mark tasks complete.
- Store recurring task rules.
- Trigger due reminders.
- Generate daily summaries.

## 3. Users and Scenarios

Primary user: one individual managing personal work and life tasks.

Example scenarios:

- User says: "明天下午3点提醒我写周报"
  - Agent detects `create_task`.
  - Tool creates task and reminder.
  - Agent confirms creation.
- User says: "把今天晚上健身改到明天早上8点"
  - Agent detects `update_task` or `reschedule_task`.
  - Tool queries matching tasks first.
  - Agent updates one clear match or asks for clarification.
- User says: "取消周五下午会议"
  - Agent detects `delete_task`.
  - Tool queries matching task.
  - Agent asks for confirmation before deletion.
- User says: "今天还有什么安排？"
  - Agent detects `query_schedule`.
  - Tool returns tasks ordered by time.
- User says: "每天早上8点学习英语"
  - Agent detects `set_recurring_task`.
  - Tool creates task with RRULE metadata.

## 4. Scope

V1 supports:

- Create task
- Update task
- Delete task
- Query schedule
- Complete task
- Set recurring task metadata
- Reminder check
- Daily summary

V1 does not support:

- Multi-user collaboration
- Shared calendars
- AI automatic scheduling
- Automatic conflict detection or auto-reschedule
- Google Calendar, Apple Calendar, or Outlook sync

## 5. Functional Requirements

### FR-001 Create Task

Input: natural language such as "明天下午3点提醒我写周报".

Intent: `create_task`

Required behavior:

- Extract title and start time.
- Resolve relative time using user timezone.
- Set default priority to `medium`.
- Set default reminder time to start time unless specified otherwise.
- Write `tasks`.
- Write `operation_logs`.

### FR-002 Update Task

Input: "把健身改到明天早上8点".

Intent: `update_task`

Required behavior:

- Query matching tasks first.
- Update only when one target is clear.
- Ask for clarification when ambiguous.
- Write `operation_logs`.

### FR-003 Delete Task

Input: "删除明天下午会议".

Intent: `delete_task`

Required behavior:

- Query matching tasks first.
- Show candidate task.
- Require explicit confirmation.
- Delete after confirmation.
- Write `operation_logs`.

### FR-004 Query Schedule

Input: "今天还有什么安排？"

Intent: `query_schedule`

Required behavior:

- Query by local day or explicit time range.
- Return tasks ordered by `start_time`.
- Never fabricate task data.

### FR-005 Complete Task

Input: "周报完成了".

Intent: `complete_task`

Required behavior:

- Query matching tasks first.
- Mark status as `done`.
- Write `operation_logs`.

### FR-006 Recurring Task

Input: "每天早上8点学习英语".

Intent: `set_recurring_task`

Required behavior:

- Store recurrence rule as RRULE text.
- V1 stores recurring metadata; recurring instance expansion can be implemented by scheduler later.

### FR-007 Reminder Check

Intent: `check_reminders`

Required behavior:

- Find pending reminders where `send_time <= now()` and `status = pending`.
- Send notification through a configured notification channel.
- Mark reminder as `sent`.
- Mark task `reminded=true` when appropriate.
- Avoid duplicate reminders.

### FR-008 Daily Summary

Intent: `daily_summary`

Required behavior:

- Summarize completed tasks.
- Summarize unfinished tasks.
- Calculate completion rate.
- Run on demand or at scheduled daily time.

## 6. Intent Definitions

Canonical intents:

- `create_task`
- `update_task`
- `delete_task`
- `query_schedule`
- `complete_task`
- `set_recurring_task`
- `check_reminders`
- `daily_summary`

Alias intent:

- `reschedule_task` maps to `update_task`.

## 7. Non-functional Requirements

- Latency: common API requests should complete in under 3 seconds.
- Availability target: 99.9% after deployment.
- Timezone: use user local timezone for parsing and display.
- Audit: all modifications must be logged.
- Data consistency: no duplicate reminders.
- Security: only authenticated clients can access task data.
- Privacy: task content is personal data and must not be exposed in logs beyond the controlled audit table.

## 8. Success Metrics

- Task creation success rate > 95%.
- Reminder delivery success rate > 99%.
- Average API response time < 3 seconds.
- User can complete at least 80% of schedule management through chat.

## 9. Roadmap

V2:

- Calendar sync
- Google Calendar
- Apple Calendar
- Outlook

V3:

- AI automatic scheduling
- Conflict detection
- Time block optimization
- Deep Work mode

V4:

- Full MCP deployment
- Multi-Agent workflows
- Voice assistant
- Wearable notifications
