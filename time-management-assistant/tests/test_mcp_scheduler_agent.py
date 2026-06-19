from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from agent.runner import AgentRunner
from app.services import TaskService
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

    service = TaskService(db_session)
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    service.create_task(
        title=unique_title,
        user_command="pytest scheduler seed",
        start_time=(now - timedelta(minutes=10)).isoformat(),
        reminder_time=(now - timedelta(minutes=5)).isoformat(),
    )

    result = worker.run_once(channels=["telegram"])

    assert result["count"] == 1
    assert worker.run_once(channels=["telegram"])["count"] == 0


def test_agent_runner_rule_mode_falls_back_without_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    parsed = AgentRunner(parser_mode="auto")._parse_command("今天有什么安排")

    assert parsed.intent == "query_schedule"
