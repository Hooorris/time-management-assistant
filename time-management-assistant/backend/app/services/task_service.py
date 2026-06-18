import uuid
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Iterator, Optional
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models import OperationIntent, ReminderChannel, TaskPriority, TaskStatus
from app.repositories import OperationLogRepository, ReminderRepository, TaskRepository
from app.services.exceptions import NotFoundError, ValidationError
from app.services.serializers import model_to_dict


ALLOWED_TASK_UPDATE_FIELDS = {
    "title",
    "description",
    "start_time",
    "end_time",
    "priority",
    "status",
    "reminder_time",
    "recurring_rule",
    "reminded",
}


class TaskService:
    def __init__(self, db: Session, *, timezone_name: str = "Asia/Shanghai") -> None:
        self.db = db
        self.timezone = ZoneInfo(timezone_name)
        self.tasks = TaskRepository(db)
        self.logs = OperationLogRepository(db)
        self.reminders = ReminderRepository(db)

    def create_task(
        self,
        *,
        title: str,
        user_command: Optional[str] = None,
        description: Optional[str] = None,
        start_time: Any = None,
        end_time: Any = None,
        priority: str = TaskPriority.MEDIUM.value,
        reminder_time: Any = None,
        recurring_rule: Optional[str] = None,
    ) -> dict[str, Any]:
        if not title:
            raise ValidationError("title is required.")
        resolved_start_time = self._parse_datetime(start_time)
        resolved_reminder_time = self._parse_datetime(reminder_time) or resolved_start_time
        with self._unit_of_work():
            task = self.tasks.create(
                title=title,
                description=description,
                start_time=resolved_start_time,
                end_time=self._parse_datetime(end_time),
                priority=priority or TaskPriority.MEDIUM.value,
                status=TaskStatus.PENDING.value,
                reminder_time=resolved_reminder_time,
                recurring_rule=recurring_rule,
                reminded=False,
            )
            if resolved_reminder_time:
                self.reminders.create(
                    task_id=task.id,
                    send_time=resolved_reminder_time,
                    channel=ReminderChannel.TELEGRAM.value,
                )
            task_id = str(task.id)
            after = model_to_dict(task)
            self.logs.create(
                intent=OperationIntent.CREATE_TASK.value,
                user_command=user_command,
                after_data=after,
            )
        return {"task_id": task_id, "task": after}

    def update_task(
        self,
        *,
        task_id: Any,
        changes: dict[str, Any],
        user_command: Optional[str] = None,
    ) -> dict[str, Any]:
        if not changes:
            raise ValidationError("changes is required.")
        normalized_changes = self._normalize_task_changes(changes)
        with self._unit_of_work():
            task = self._get_task_or_raise(task_id)
            before = model_to_dict(task)
            updated = self.tasks.update(task, **normalized_changes)
            after = model_to_dict(updated)
            self.logs.create(
                intent=OperationIntent.UPDATE_TASK.value,
                user_command=user_command,
                before_data=before,
                after_data=after,
            )
        return {"task": after, "before": before}

    def delete_task(
        self,
        *,
        task_id: Any,
        user_command: Optional[str] = None,
    ) -> dict[str, Any]:
        with self._unit_of_work():
            task = self._get_task_or_raise(task_id)
            before = model_to_dict(task)
            self.tasks.delete(task)
            self.logs.create(
                intent=OperationIntent.DELETE_TASK.value,
                user_command=user_command,
                before_data=before,
                after_data=None,
            )
        return {"deleted_task": before}

    def query_schedule(
        self,
        *,
        date_value: Any = None,
        start_time_from: Any = None,
        start_time_to: Any = None,
        include_done: bool = True,
        query: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        start, end = self._resolve_range(date_value, start_time_from, start_time_to)
        tasks = self.tasks.list(
            query=query,
            status=status,
            start_time_from=start,
            start_time_to=end,
            include_done=include_done,
            limit=limit,
        )
        return {"tasks": [model_to_dict(task) for task in tasks]}

    def complete_task(
        self,
        *,
        task_id: Any,
        user_command: Optional[str] = None,
    ) -> dict[str, Any]:
        with self._unit_of_work():
            task = self._get_task_or_raise(task_id)
            before = model_to_dict(task)
            updated = self.tasks.update(
                task,
                status=TaskStatus.DONE.value,
                reminded=True,
            )
            after = model_to_dict(updated)
            self.logs.create(
                intent=OperationIntent.COMPLETE_TASK.value,
                user_command=user_command,
                before_data=before,
                after_data=after,
            )
        return {"task": after, "before": before}

    def set_recurring_task(
        self,
        *,
        recurring_rule: str,
        task_id: Any = None,
        user_command: Optional[str] = None,
        title: Optional[str] = None,
        start_time: Any = None,
        reminder_time: Any = None,
    ) -> dict[str, Any]:
        if not recurring_rule:
            raise ValidationError("recurring_rule is required.")
        if task_id:
            changes: dict[str, Any] = {"recurring_rule": recurring_rule}
            if start_time is not None:
                changes["start_time"] = start_time
            if reminder_time is not None:
                changes["reminder_time"] = reminder_time
            normalized_changes = self._normalize_task_changes(changes)
            with self._unit_of_work():
                task = self._get_task_or_raise(task_id)
                before = model_to_dict(task)
                updated = self.tasks.update(task, **normalized_changes)
                after = model_to_dict(updated)
                self.logs.create(
                    intent=OperationIntent.SET_RECURRING_TASK.value,
                    user_command=user_command,
                    before_data=before,
                    after_data=after,
                )
            return {"task": after, "before": before}
        if not title:
            raise ValidationError("title is required when task_id is not provided.")
        resolved_start_time = self._parse_datetime(start_time)
        resolved_reminder_time = self._parse_datetime(reminder_time) or resolved_start_time
        with self._unit_of_work():
            task = self.tasks.create(
                title=title,
                start_time=resolved_start_time,
                reminder_time=resolved_reminder_time,
                recurring_rule=recurring_rule,
                priority=TaskPriority.MEDIUM.value,
                status=TaskStatus.PENDING.value,
                reminded=False,
            )
            if resolved_reminder_time:
                self.reminders.create(
                    task_id=task.id,
                    send_time=resolved_reminder_time,
                    channel=ReminderChannel.TELEGRAM.value,
                )
            after = model_to_dict(task)
            self.logs.create(
                intent=OperationIntent.SET_RECURRING_TASK.value,
                user_command=user_command,
                after_data=after,
            )
        return {"task": after}

    def check_reminders(
        self,
        *,
        now: Any = None,
        channels: Optional[list[str]] = None,
        user_command: Optional[str] = None,
    ) -> dict[str, Any]:
        current_time = self._parse_datetime(now) or datetime.now(timezone.utc)
        with self._unit_of_work():
            due_reminders = self.reminders.list_due(now=current_time, channels=channels)
            before = [model_to_dict(reminder) for reminder in due_reminders]
            after: list[dict[str, Any]] = []
            for reminder in due_reminders:
                self.reminders.mark_sent(reminder, sent_at=current_time)
                task = self.tasks.get_by_id(reminder.task_id)
                if task:
                    self.tasks.update(task, reminded=True)
                after.append(model_to_dict(reminder))
            if due_reminders:
                self.logs.create(
                    intent=OperationIntent.CHECK_REMINDERS.value,
                    user_command=user_command,
                    before_data={"reminders": before},
                    after_data={"reminders": after},
                )
        return {"reminders": after, "count": len(after)}

    def daily_summary(self, *, date_value: Any = None) -> dict[str, Any]:
        schedule = self.query_schedule(date_value=date_value, include_done=True)
        tasks = schedule["tasks"]
        completed = [task for task in tasks if task["status"] == TaskStatus.DONE.value]
        unfinished = [task for task in tasks if task["status"] != TaskStatus.DONE.value]
        completion_rate = round((len(completed) / len(tasks)) * 100, 2) if tasks else 0
        return {
            "completed": completed,
            "unfinished": unfinished,
            "completion_rate": completion_rate,
        }

    def _get_task_or_raise(self, task_id: Any):
        task = self.tasks.get_by_id(self._parse_uuid(task_id))
        if not task:
            raise NotFoundError("Task not found.")
        return task

    @contextmanager
    def _unit_of_work(self) -> Iterator[None]:
        try:
            yield
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

    def _normalize_task_changes(self, changes: dict[str, Any]) -> dict[str, Any]:
        invalid_fields = sorted(set(changes) - ALLOWED_TASK_UPDATE_FIELDS)
        if invalid_fields:
            raise ValidationError(f"Unsupported task fields: {', '.join(invalid_fields)}")
        normalized = dict(changes)
        for field in ("start_time", "end_time", "reminder_time"):
            if field in normalized:
                normalized[field] = self._parse_datetime(normalized[field])
        return normalized

    def _resolve_range(
        self,
        date_value: Any,
        start_time_from: Any,
        start_time_to: Any,
    ) -> tuple[Optional[datetime], Optional[datetime]]:
        if start_time_from or start_time_to:
            return self._parse_datetime(start_time_from), self._parse_datetime(start_time_to)
        if date_value is None:
            return None, None
        day = self._parse_date(date_value)
        start = datetime.combine(day, time.min, tzinfo=self.timezone)
        return start, start + timedelta(days=1)

    def _parse_date(self, value: Any) -> date:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.astimezone(self.timezone).date()
        if isinstance(value, str):
            if value == "today":
                return datetime.now(self.timezone).date()
            if value == "tomorrow":
                return datetime.now(self.timezone).date() + timedelta(days=1)
            if value == "yesterday":
                return datetime.now(self.timezone).date() - timedelta(days=1)
            return date.fromisoformat(value)
        raise ValidationError("Invalid date value.")

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=self.timezone)
            return value
        if isinstance(value, str):
            parsed = datetime.fromisoformat(value)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=self.timezone)
            return parsed
        raise ValidationError("Invalid datetime value.")

    def _parse_uuid(self, value: Any) -> uuid.UUID:
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))
