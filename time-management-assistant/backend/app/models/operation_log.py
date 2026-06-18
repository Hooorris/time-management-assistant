import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import CheckConstraint, DateTime, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class OperationLog(Base):
    __tablename__ = "operation_logs"
    __table_args__ = (
        CheckConstraint(
            "intent IN ("
            "'create_task', 'update_task', 'delete_task', 'query_schedule', "
            "'complete_task', 'set_recurring_task', 'check_reminders', 'daily_summary'"
            ")",
            name="operation_logs_intent_check",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_command: Mapped[Optional[str]] = mapped_column(Text)
    intent: Mapped[str] = mapped_column(Text, nullable=False)
    before_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    after_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
