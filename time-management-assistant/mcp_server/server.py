import sys
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(BACKEND_ROOT / ".env")

from app.config import get_settings  # noqa: E402
from app.database import get_session_local  # noqa: E402
from app.services import NotFoundError, TaskService, ValidationError  # noqa: E402
from app.services.serializers import model_to_dict  # noqa: E402


mcp = FastMCP("time-management-assistant")


def _validate_mcp_auth_config() -> None:
    settings = get_settings()
    if settings.mcp_auth_required and not settings.mcp_auth_token:
        raise RuntimeError("MCP_AUTH_TOKEN is required when MCP_AUTH_REQUIRED=true.")


@contextmanager
def _service_context(timezone: str = "Asia/Shanghai") -> Iterator[TaskService]:
    _validate_mcp_auth_config()
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield TaskService(db, timezone_name=timezone)
    finally:
        db.close()


def _task_id_to_uuid(task_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(task_id))
    except ValueError as exc:
        raise ValidationError("Invalid task_id.") from exc


@mcp.tool()
def create_task(
    title: str,
    user_command: Optional[str] = None,
    description: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    priority: str = "medium",
    reminder_time: Optional[str] = None,
    recurring_rule: Optional[str] = None,
) -> dict[str, Any]:
    """Create a new task or reminder."""
    with _service_context() as service:
        return service.create_task(
            title=title,
            user_command=user_command,
            description=description,
            start_time=start_time,
            end_time=end_time,
            priority=priority,
            reminder_time=reminder_time,
            recurring_rule=recurring_rule,
        )


@mcp.tool()
def update_task(
    task_id: str,
    changes: dict[str, Any],
    user_command: Optional[str] = None,
) -> dict[str, Any]:
    """Update an existing task."""
    with _service_context() as service:
        return service.update_task(
            task_id=task_id,
            changes=changes,
            user_command=user_command,
        )


@mcp.tool()
def delete_task(
    task_id: str,
    user_command: Optional[str] = None,
) -> dict[str, Any]:
    """Delete an existing task after explicit user confirmation."""
    with _service_context() as service:
        return service.delete_task(task_id=task_id, user_command=user_command)


@mcp.tool()
def query_task(
    task_id: Optional[str] = None,
    query: Optional[str] = None,
    date: Optional[str] = None,
    start_time_from: Optional[str] = None,
    start_time_to: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Find tasks by id, title query, status, local day, or time range."""
    with _service_context() as service:
        if task_id:
            task = service.tasks.get_by_id(_task_id_to_uuid(task_id))
            if not task:
                raise NotFoundError("Task not found.")
            return {"tasks": [model_to_dict(task)]}
        return service.query_schedule(
            date_value=date,
            start_time_from=start_time_from,
            start_time_to=start_time_to,
            include_done=True,
            query=query,
            status=status,
            limit=limit,
        )


@mcp.tool()
def list_today_tasks(
    timezone: str = "Asia/Shanghai",
    include_done: bool = True,
) -> dict[str, Any]:
    """List today's tasks in the user's local timezone."""
    with _service_context(timezone) as service:
        return service.query_schedule(date_value="today", include_done=include_done)


@mcp.tool()
def query_schedule(
    date: Optional[str] = None,
    start_time_from: Optional[str] = None,
    start_time_to: Optional[str] = None,
    include_done: bool = True,
    timezone: str = "Asia/Shanghai",
) -> dict[str, Any]:
    """Query schedule by local date or explicit time range."""
    with _service_context(timezone) as service:
        return service.query_schedule(
            date_value=date,
            start_time_from=start_time_from,
            start_time_to=start_time_to,
            include_done=include_done,
        )


@mcp.tool()
def complete_task(
    task_id: str,
    user_command: Optional[str] = None,
) -> dict[str, Any]:
    """Mark a task as done."""
    with _service_context() as service:
        return service.complete_task(task_id=task_id, user_command=user_command)


@mcp.tool()
def set_recurring_task(
    recurring_rule: str,
    user_command: Optional[str] = None,
    task_id: Optional[str] = None,
    title: Optional[str] = None,
    start_time: Optional[str] = None,
    reminder_time: Optional[str] = None,
) -> dict[str, Any]:
    """Create a new recurring task or attach recurrence metadata to an existing task."""
    with _service_context() as service:
        return service.set_recurring_task(
            recurring_rule=recurring_rule,
            task_id=task_id,
            user_command=user_command,
            title=title,
            start_time=start_time,
            reminder_time=reminder_time,
        )


@mcp.tool()
def daily_summary(
    date: Optional[str] = None,
    timezone: str = "Asia/Shanghai",
) -> dict[str, Any]:
    """Generate a daily summary."""
    with _service_context(timezone) as service:
        return service.daily_summary(date_value=date)


@mcp.tool()
def check_reminders(
    now: Optional[str] = None,
    channels: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Find and mark due reminders."""
    with _service_context() as service:
        return service.check_reminders(
            now=now or datetime.now().astimezone().isoformat(),
            channels=channels,
            user_command="mcp reminder scan",
        )


def main() -> None:
    _validate_mcp_auth_config()
    mcp.run()


if __name__ == "__main__":
    main()
