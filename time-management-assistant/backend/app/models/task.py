import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import TaskPriority, TaskStatus


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("priority IN ('low', 'medium', 'high')", name="tasks_priority_check"),
        CheckConstraint("status IN ('pending', 'done', 'cancelled')", name="tasks_status_check"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    priority: Mapped[str] = mapped_column(Text, nullable=False, default=TaskPriority.MEDIUM.value, server_default="medium")
    status: Mapped[str] = mapped_column(Text, nullable=False, default=TaskStatus.PENDING.value, server_default="pending")
    reminder_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    recurring_rule: Mapped[Optional[str]] = mapped_column(Text)
    reminded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    reminders: Mapped[list["Reminder"]] = relationship(
        "Reminder",
        back_populates="task",
        cascade="all, delete-orphan",
    )
