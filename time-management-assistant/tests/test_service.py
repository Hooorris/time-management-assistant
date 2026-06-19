from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.services import TaskService


def test_task_service_crud_summary_and_reminders(db_session, unique_title: str) -> None:
    service = TaskService(db_session)
    now = datetime.now(ZoneInfo("Asia/Shanghai"))

    created = service.create_task(
        title=unique_title,
        user_command="pytest create",
        start_time=(now - timedelta(minutes=10)).isoformat(),
        reminder_time=(now - timedelta(minutes=5)).isoformat(),
    )
    task_id = created["task_id"]

    schedule = service.query_schedule(date_value=now.date().isoformat(), query=unique_title)
    assert len(schedule["tasks"]) == 1

    updated = service.update_task(
        task_id=task_id,
        changes={"priority": "high"},
        user_command="pytest update",
    )
    assert updated["task"]["priority"] == "high"

    reminder_scan = service.check_reminders(now=now.isoformat(), channels=["telegram"], user_command="pytest reminders")
    assert reminder_scan["count"] == 1

    duplicate_scan = service.check_reminders(now=now.isoformat(), channels=["telegram"], user_command="pytest reminders")
    assert duplicate_scan["count"] == 0

    completed = service.complete_task(task_id=task_id, user_command="pytest complete")
    assert completed["task"]["status"] == "done"

    summary = service.daily_summary(date_value=now.date().isoformat())
    assert any(task["id"] == task_id for task in summary["completed"])

    deleted = service.delete_task(task_id=task_id, user_command="pytest delete")
    assert deleted["deleted_task"]["id"] == task_id
