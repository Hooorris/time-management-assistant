from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_task_service
from app.database import get_db
from app.schemas import (
    CompleteTaskRequest,
    CreateTaskRequest,
    DeleteTaskRequest,
    DeleteTaskResponse,
    TaskListResponse,
    TaskResponse,
    TaskWithBeforeResponse,
    UpdateTaskRequest,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/create", operation_id="create_task", response_model=TaskResponse)
def create_task(payload: CreateTaskRequest, db: Session = Depends(get_db)) -> dict:
    service = get_task_service(db)
    return service.create_task(
        user_command=payload.user_command,
        title=payload.title,
        description=payload.description,
        start_time=payload.start_time,
        end_time=payload.end_time,
        priority=payload.priority,
        reminder_time=payload.reminder_time,
        recurring_rule=payload.recurring_rule,
    )


@router.post("/update", operation_id="update_task", response_model=TaskWithBeforeResponse)
def update_task(payload: UpdateTaskRequest, db: Session = Depends(get_db)) -> dict:
    service = get_task_service(db)
    return service.update_task(
        user_command=payload.user_command,
        task_id=payload.task_id,
        changes=payload.changes,
    )


@router.post("/delete", operation_id="delete_task", response_model=DeleteTaskResponse)
def delete_task(payload: DeleteTaskRequest, db: Session = Depends(get_db)) -> dict:
    service = get_task_service(db)
    return service.delete_task(
        user_command=payload.user_command,
        task_id=payload.task_id,
    )


@router.get("/query", operation_id="query_schedule", response_model=TaskListResponse)
def query_schedule(
    date: Optional[str] = None,
    query: Optional[str] = None,
    status: Optional[str] = None,
    start_time_from: Optional[str] = None,
    start_time_to: Optional[str] = None,
    include_done: bool = True,
    timezone: str = "Asia/Shanghai",
    db: Session = Depends(get_db),
) -> dict:
    service = get_task_service(db, timezone_name=timezone)
    return service.query_schedule(
        date_value=date,
        start_time_from=start_time_from,
        start_time_to=start_time_to,
        include_done=include_done,
        query=query,
        status=status,
    )


@router.post("/complete", operation_id="complete_task", response_model=TaskWithBeforeResponse)
def complete_task(payload: CompleteTaskRequest, db: Session = Depends(get_db)) -> dict:
    service = get_task_service(db)
    return service.complete_task(
        user_command=payload.user_command,
        task_id=payload.task_id,
    )
