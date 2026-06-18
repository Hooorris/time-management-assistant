import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.models import Task


class TaskRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, **values: Any) -> Task:
        task = Task(**values)
        self.db.add(task)
        self.db.flush()
        self.db.refresh(task)
        return task

    def get_by_id(self, task_id: uuid.UUID) -> Optional[Task]:
        return self.db.get(Task, task_id)

    def list(
        self,
        *,
        query: Optional[str] = None,
        status: Optional[str] = None,
        start_time_from: Optional[datetime] = None,
        start_time_to: Optional[datetime] = None,
        include_done: bool = True,
        limit: int = 100,
    ) -> list[Task]:
        statement: Select[tuple[Task]] = select(Task)
        if query:
            pattern = f"%{query}%"
            statement = statement.where(
                or_(Task.title.ilike(pattern), Task.description.ilike(pattern))
            )
        if status:
            statement = statement.where(Task.status == status)
        elif not include_done:
            statement = statement.where(Task.status != "done")
        if start_time_from:
            statement = statement.where(Task.start_time >= start_time_from)
        if start_time_to:
            statement = statement.where(Task.start_time < start_time_to)
        statement = statement.order_by(Task.start_time.nulls_last(), Task.created_at).limit(limit)
        return list(self.db.scalars(statement))

    def update(self, task: Task, **changes: Any) -> Task:
        for field, value in changes.items():
            setattr(task, field, value)
        self.db.flush()
        self.db.refresh(task)
        return task

    def delete(self, task: Task) -> Task:
        self.db.delete(task)
        self.db.flush()
        return task
