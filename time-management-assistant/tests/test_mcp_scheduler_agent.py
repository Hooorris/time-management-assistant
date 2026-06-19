from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from agent.runner import AgentRunner
from app.models import Reminder, Task
from app.services import TaskService
from notifications import NotificationResult
from mcp_server import server as mcp_server
from scheduler import worker


@pytest.mark.asyncio
async def test_mcp_registers_expected_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_AUTH_REQUIRED", "false")
    tools = await mcp_server.mcp.list_tools()
    names = {tool.name for tool in tools}

    assert names == {
        "create_task",
        "update_task",
        "delete_task",
        "query_task",
        "list_today_tasks",
        "query_schedule",
        "complete_task",
        "set_recurring_task",
        "daily_summary",
        "check_reminders",
    }


def test_scheduler_run_once_marks_due_reminder(db_session, unique_title: str, monkeypatch: pytest.MonkeyPatch) -> None:
    class SessionFactory:
        def __call__(self):
            return db_session

    monkeypatch.setattr(worker, "get_session_local", lambda: SessionFactory())

    service = TaskService(db_session, default_reminder_channel="bark")
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    service.create_task(
        title=unique_title,
        user_command="pytest scheduler seed",
        start_time=(now - timedelta(minutes=10)).isoformat(),
        reminder_time=(now - timedelta(minutes=5)).isoformat(),
    )

    result = worker.run_once(channels=["bark"])

    assert result["count"] == 1
    assert worker.run_once(channels=["bark"])["count"] == 0


def test_scheduler_sends_bark_and_marks_sent(db_session, unique_title: str, monkeypatch: pytest.MonkeyPatch) -> None:
    class SessionFactory:
        def __call__(self):
            return db_session

    class FakeNotifier:
        def __init__(self):
            self.calls = []

        def send(self, message):
            self.calls.append(message)
            return NotificationResult(success=True, channel=message.channel)

    monkeypatch.setattr(worker, "get_session_local", lambda: SessionFactory())

    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    task = Task(
        title=unique_title,
        start_time=now - timedelta(minutes=10),
        reminder_time=now - timedelta(minutes=5),
        reminded=False,
    )
    db_session.add(task)
    db_session.flush()
    reminder = Reminder(
        task_id=task.id,
        send_time=now - timedelta(minutes=5),
        channel="bark",
    )
    db_session.add(reminder)
    db_session.flush()
    task_id = task.id
    reminder_id = reminder.id
    db_session.commit()

    notifier = FakeNotifier()
    result = worker.run_once(channels=["bark"], notifier=notifier)
    updated_task = db_session.get(Task, task_id)
    updated_reminder = db_session.get(Reminder, reminder_id)

    assert result["count"] == 1
    assert result["sent_count"] == 1
    assert result["failed_count"] == 0
    assert updated_reminder.status == "sent"
    assert updated_reminder.sent_at is not None
    assert updated_task.reminded is True
    assert len(notifier.calls) == 1

    assert worker.run_once(channels=["bark"], notifier=notifier)["count"] == 0
    assert len(notifier.calls) == 1


def test_scheduler_marks_failed_when_bark_fails(db_session, unique_title: str, monkeypatch: pytest.MonkeyPatch) -> None:
    class SessionFactory:
        def __call__(self):
            return db_session

    class FakeNotifier:
        def __init__(self):
            self.calls = []

        def send(self, message):
            self.calls.append(message)
            return NotificationResult(
                success=False,
                channel=message.channel,
                error_message="bark failed",
            )

    monkeypatch.setattr(worker, "get_session_local", lambda: SessionFactory())

    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    task = Task(
        title=unique_title,
        start_time=now - timedelta(minutes=10),
        reminder_time=now - timedelta(minutes=5),
        reminded=False,
    )
    db_session.add(task)
    db_session.flush()
    reminder = Reminder(
        task_id=task.id,
        send_time=now - timedelta(minutes=5),
        channel="bark",
    )
    db_session.add(reminder)
    db_session.flush()
    task_id = task.id
    reminder_id = reminder.id
    db_session.commit()

    notifier = FakeNotifier()
    result = worker.run_once(channels=["bark"], notifier=notifier)
    updated_task = db_session.get(Task, task_id)
    updated_reminder = db_session.get(Reminder, reminder_id)

    assert result["count"] == 1
    assert result["sent_count"] == 0
    assert result["failed_count"] == 1
    assert updated_reminder.status == "failed"
    assert updated_reminder.error_message == "bark failed"
    assert updated_task.reminded is False
    assert len(notifier.calls) == 1

    assert worker.run_once(channels=["bark"], notifier=notifier)["count"] == 0
    assert len(notifier.calls) == 1


def test_scheduler_sends_wechat_work_and_marks_sent(
    db_session, unique_title: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    class SessionFactory:
        def __call__(self):
            return db_session

    class FakeNotifier:
        def __init__(self):
            self.calls = []

        def send(self, message):
            self.calls.append(message)
            return NotificationResult(success=True, channel=message.channel)

    monkeypatch.setattr(worker, "get_session_local", lambda: SessionFactory())

    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    task = Task(
        title=unique_title,
        start_time=now - timedelta(minutes=10),
        reminder_time=now - timedelta(minutes=5),
        reminded=False,
    )
    db_session.add(task)
    db_session.flush()
    reminder = Reminder(
        task_id=task.id,
        send_time=now - timedelta(minutes=5),
        channel="wechat_work",
    )
    db_session.add(reminder)
    db_session.flush()
    task_id = task.id
    reminder_id = reminder.id
    db_session.commit()

    notifier = FakeNotifier()
    result = worker.run_once(channels=["wechat_work"], notifier=notifier)
    updated_task = db_session.get(Task, task_id)
    updated_reminder = db_session.get(Reminder, reminder_id)

    assert result["count"] == 1
    assert result["sent_count"] == 1
    assert updated_reminder.status == "sent"
    assert updated_task.reminded is True
    assert len(notifier.calls) == 1
    assert notifier.calls[0].channel == "wechat_work"

    assert worker.run_once(channels=["wechat_work"], notifier=notifier)["count"] == 0
    assert len(notifier.calls) == 1


def test_agent_runner_rule_mode_falls_back_without_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    parsed = AgentRunner(parser_mode="auto")._parse_command("今天有什么安排")

    assert parsed.intent == "query_schedule"
