import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(BACKEND_ROOT / ".env")

from app.database import get_session_local  # noqa: E402
from app.services import TaskService  # noqa: E402

from agent.parser import ChineseCommandParser, ParsedCommand


class AgentRunner:
    def __init__(self, timezone_name: str = "Asia/Shanghai") -> None:
        self.timezone_name = timezone_name
        self.parser = ChineseCommandParser(timezone_name)

    def handle_once(self, command: str, *, confirm_delete: bool = False) -> str:
        parsed = self.parser.parse(command)
        if parsed.clarification:
            return parsed.clarification
        with self._service_context() as service:
            if parsed.intent == "create_task":
                result = service.create_task(
                    title=parsed.title or "",
                    user_command=command,
                    start_time=parsed.start_time,
                    reminder_time=parsed.reminder_time,
                )
                return self._format_task_created(result["task"])
            if parsed.intent == "query_schedule":
                result = service.query_schedule(date_value=parsed.date, include_done=True)
                return self._format_task_list(result["tasks"], empty_text="这一天暂无安排。")
            if parsed.intent == "update_task":
                return self._handle_update(service, parsed, command)
            if parsed.intent == "delete_task":
                return self._handle_delete(
                    service,
                    parsed,
                    command,
                    confirm_delete=confirm_delete,
                )
            if parsed.intent == "complete_task":
                return self._handle_complete(service, parsed, command)
            if parsed.intent == "set_recurring_task":
                result = service.set_recurring_task(
                    title=parsed.title,
                    start_time=parsed.start_time,
                    reminder_time=parsed.reminder_time,
                    recurring_rule=parsed.recurring_rule or "",
                    user_command=command,
                )
                return self._format_task_created(result["task"], prefix="已创建重复任务")
            if parsed.intent == "daily_summary":
                result = service.daily_summary(date_value=parsed.date)
                return self._format_daily_summary(result)
            if parsed.intent == "check_reminders":
                result = service.check_reminders(
                    now=parsed.start_time,
                    channels=["telegram"],
                    user_command=command,
                )
                return f"提醒扫描完成，到期提醒 {result['count']} 条。"
        return "我还不能处理这条指令。"

    def handle_delete_with_prompt(self, command: str) -> str:
        parsed = self.parser.parse(command)
        if parsed.clarification:
            return parsed.clarification
        if parsed.intent != "delete_task":
            return self.handle_once(command)
        with self._service_context() as service:
            matches = self._find_matches(service, parsed, include_done=True)
            if not matches:
                return "没有找到匹配的任务。"
            if len(matches) > 1:
                return self._format_task_list(matches, empty_text="", prefix="找到多个匹配任务，请输入更明确的任务名称：")
            task = matches[0]
            print("将删除以下任务：")
            print(self._format_task(task, index=1))
            answer = input("确认删除吗？输入 yes 删除，其它输入取消：").strip().lower()
            if answer != "yes":
                return "已取消删除。"
            result = service.delete_task(task_id=task["id"], user_command=command)
            return f"已删除：{result['deleted_task']['title']}"

    @contextmanager
    def _service_context(self) -> Iterator[TaskService]:
        SessionLocal = get_session_local()
        db = SessionLocal()
        try:
            yield TaskService(db, timezone_name=self.timezone_name)
        finally:
            db.close()

    def _handle_update(self, service: TaskService, parsed: ParsedCommand, command: str) -> str:
        matches = self._find_matches(service, parsed, include_done=False)
        if not matches:
            return "没有找到要修改的任务。"
        if len(matches) > 1:
            return self._format_task_list(matches, empty_text="", prefix="找到多个匹配任务，请输入更明确的任务名称：")
        result = service.update_task(
            task_id=matches[0]["id"],
            changes=parsed.changes,
            user_command=command,
        )
        task = result["task"]
        return f"已更新：{task['title']} -> {self._format_time(task.get('start_time'))}"

    def _handle_delete(
        self,
        service: TaskService,
        parsed: ParsedCommand,
        command: str,
        *,
        confirm_delete: bool,
    ) -> str:
        matches = self._find_matches(service, parsed, include_done=True)
        if not matches:
            return "没有找到匹配的任务。"
        if len(matches) > 1:
            return self._format_task_list(matches, empty_text="", prefix="找到多个匹配任务，请输入更明确的任务名称：")
        if not confirm_delete:
            return "删除前需要确认：\n" + self._format_task(matches[0], index=1)
        result = service.delete_task(task_id=matches[0]["id"], user_command=command)
        return f"已删除：{result['deleted_task']['title']}"

    def _handle_complete(self, service: TaskService, parsed: ParsedCommand, command: str) -> str:
        matches = self._find_matches(service, parsed, include_done=False)
        if not matches:
            return "没有找到要标记完成的任务。"
        if len(matches) > 1:
            return self._format_task_list(matches, empty_text="", prefix="找到多个匹配任务，请输入更明确的任务名称：")
        result = service.complete_task(task_id=matches[0]["id"], user_command=command)
        return f"已完成：{result['task']['title']}"

    def _find_matches(
        self,
        service: TaskService,
        parsed: ParsedCommand,
        *,
        include_done: bool,
    ) -> list[dict]:
        result = service.query_schedule(
            date_value=parsed.date,
            query=parsed.query,
            include_done=include_done,
            limit=10,
        )
        return result["tasks"]

    def _format_task_created(self, task: dict, *, prefix: str = "已创建任务") -> str:
        return f"{prefix}：{task['title']} @ {self._format_time(task.get('start_time'))}"

    def _format_task_list(
        self,
        tasks: list[dict],
        *,
        empty_text: str,
        prefix: Optional[str] = None,
    ) -> str:
        if not tasks:
            return empty_text
        lines = [prefix] if prefix else []
        lines.extend(self._format_task(task, index=index) for index, task in enumerate(tasks, start=1))
        return "\n".join(lines)

    def _format_task(self, task: dict, *, index: int) -> str:
        return (
            f"{index}. {task['title']} | "
            f"{self._format_time(task.get('start_time'))} | "
            f"status={task.get('status')} | reminded={task.get('reminded')}"
        )

    def _format_daily_summary(self, summary: dict) -> str:
        completed = summary["completed"]
        unfinished = summary["unfinished"]
        lines = ["完成："]
        lines.extend(f"- {task['title']}" for task in completed) if completed else lines.append("- 无")
        lines.append("未完成：")
        lines.extend(f"- {task['title']}" for task in unfinished) if unfinished else lines.append("- 无")
        lines.append(f"完成率：{summary['completion_rate']}%")
        return "\n".join(lines)

    def _format_time(self, value: Optional[str]) -> str:
        if not value:
            return "未设置时间"
        return value.replace("T", " ")
