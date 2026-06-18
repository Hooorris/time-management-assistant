from enum import Enum


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskStatus(str, Enum):
    PENDING = "pending"
    DONE = "done"
    CANCELLED = "cancelled"


class ReminderChannel(str, Enum):
    TELEGRAM = "telegram"
    EMAIL = "email"
    BARK = "bark"
    WECHAT_WORK = "wechat_work"
    DINGTALK = "dingtalk"


class ReminderStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OperationIntent(str, Enum):
    CREATE_TASK = "create_task"
    UPDATE_TASK = "update_task"
    DELETE_TASK = "delete_task"
    QUERY_SCHEDULE = "query_schedule"
    COMPLETE_TASK = "complete_task"
    SET_RECURRING_TASK = "set_recurring_task"
    CHECK_REMINDERS = "check_reminders"
    DAILY_SUMMARY = "daily_summary"
