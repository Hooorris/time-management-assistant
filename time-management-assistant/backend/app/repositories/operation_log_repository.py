from typing import Any, Optional

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import OperationLog


class OperationLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        intent: str,
        user_command: Optional[str] = None,
        before_data: Optional[dict[str, Any]] = None,
        after_data: Optional[dict[str, Any]] = None,
    ) -> OperationLog:
        log = OperationLog(
            user_command=user_command,
            intent=intent,
            before_data=before_data,
            after_data=after_data,
        )
        self.db.add(log)
        self.db.flush()
        self.db.refresh(log)
        return log

    def list_recent(self, *, limit: int = 100) -> list[OperationLog]:
        statement: Select[tuple[OperationLog]] = (
            select(OperationLog)
            .order_by(OperationLog.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(statement))
