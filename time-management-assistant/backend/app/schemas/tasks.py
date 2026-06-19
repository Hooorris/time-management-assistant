from typing import Any, Optional

from pydantic import BaseModel, Field


class TaskSchema(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    priority: str
    status: str
    reminder_time: Optional[str] = None
    recurring_rule: Optional[str] = None
    reminded: bool
    created_at: str
    updated_at: str


class ReminderSchema(BaseModel):
    id: str
    task_id: str
    send_time: str
    channel: str
    status: str
    sent_at: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


class CreateTaskRequest(BaseModel):
    user_command: Optional[str] = None
    title: str
    description: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    priority: str = "medium"
    reminder_time: Optional[str] = None
    recurring_rule: Optional[str] = None


class UpdateTaskRequest(BaseModel):
    user_command: Optional[str] = None
    task_id: str
    changes: dict[str, Any]


class DeleteTaskRequest(BaseModel):
    user_command: Optional[str] = None
    task_id: str


class CompleteTaskRequest(BaseModel):
    user_command: Optional[str] = None
    task_id: str


class DailySummaryRequest(BaseModel):
    date: Optional[str] = None
    timezone: str = "Asia/Shanghai"


class CheckRemindersRequest(BaseModel):
    now: Optional[str] = None
    channels: Optional[list[str]] = None
    user_command: Optional[str] = None


class TaskResponse(BaseModel):
    task_id: str
    task: TaskSchema


class TaskWithBeforeResponse(BaseModel):
    task: TaskSchema
    before: TaskSchema


class DeleteTaskResponse(BaseModel):
    deleted_task: TaskSchema


class TaskListResponse(BaseModel):
    tasks: list[TaskSchema]


class ReminderCheckResponse(BaseModel):
    reminders: list[ReminderSchema]
    count: int


class DailySummaryResponse(BaseModel):
    completed: list[TaskSchema]
    unfinished: list[TaskSchema]
    completion_rate: float = Field(ge=0)


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
