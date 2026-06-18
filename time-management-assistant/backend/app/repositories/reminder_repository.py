import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import Reminder


class ReminderRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, **values: Any) -> Reminder:
        reminder = Reminder(**values)
        self.db.add(reminder)
        self.db.flush()
        self.db.refresh(reminder)
        return reminder

    def list_due(
        self,
        *,
        now: datetime,
        channels: Optional[list[str]] = None,
        limit: int = 100,
    ) -> list[Reminder]:
        statement: Select[tuple[Reminder]] = (
            select(Reminder)
            .where(Reminder.send_time <= now)
            .where(Reminder.status == "pending")
        )
        if channels:
            statement = statement.where(Reminder.channel.in_(channels))
        statement = statement.order_by(Reminder.send_time, Reminder.created_at).limit(limit)
        return list(self.db.scalars(statement))

    def mark_sent(self, reminder: Reminder, *, sent_at: datetime) -> Reminder:
        reminder.status = "sent"
        reminder.sent_at = sent_at
        reminder.error_message = None
        self.db.flush()
        self.db.refresh(reminder)
        return reminder

    def mark_failed(self, reminder: Reminder, *, error_message: str) -> Reminder:
        reminder.status = "failed"
        reminder.error_message = error_message
        self.db.flush()
        self.db.refresh(reminder)
        return reminder

    def count_by_task_id(self, task_id: uuid.UUID) -> int:
        statement = select(Reminder).where(Reminder.task_id == task_id)
        return len(list(self.db.scalars(statement)))
