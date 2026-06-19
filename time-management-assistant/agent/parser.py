import re
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo


WEEKDAYS = {
    "一": 0,
    "二": 1,
    "三": 2,
    "四": 3,
    "五": 4,
    "六": 5,
    "日": 6,
    "天": 6,
}

BYDAY = {
    "一": "MO",
    "二": "TU",
    "三": "WE",
    "四": "TH",
    "五": "FR",
    "六": "SA",
    "日": "SU",
    "天": "SU",
}

DATE_PATTERN = re.compile(r"(今天|明天|后天|昨天|本周[一二三四五六日天]|下周[一二三四五六日天]|周[一二三四五六日天])")
TIME_PATTERN = re.compile(r"(凌晨|早上|上午|中午|下午|晚上)?\s*(\d{1,2})(?:[:：](\d{1,2})|点(半|[0-5]?\d分?)?)")


@dataclass
class ParsedCommand:
    intent: str
    user_command: str
    title: Optional[str] = None
    query: Optional[str] = None
    date: Optional[str] = None
    start_time: Optional[str] = None
    reminder_time: Optional[str] = None
    recurring_rule: Optional[str] = None
    changes: dict[str, Any] = field(default_factory=dict)
    clarification: Optional[str] = None


class ChineseCommandParser:
    def __init__(self, timezone_name: str = "Asia/Shanghai") -> None:
        self.timezone = ZoneInfo(timezone_name)

    def parse(self, text: str, *, now: Optional[datetime] = None) -> ParsedCommand:
        command = text.strip()
        current = now or datetime.now(self.timezone)
        if not command:
            return ParsedCommand(
                intent="unknown",
                user_command=text,
                clarification="请输入要管理的日程指令。",
            )

        if self._is_daily_summary(command):
            return ParsedCommand(
                intent="daily_summary",
                user_command=command,
                date=self._resolve_date(command, current).isoformat(),
            )
        if self._is_reminder_check(command):
            return ParsedCommand(
                intent="check_reminders",
                user_command=command,
                start_time=current.isoformat(),
            )
        if self._is_query(command):
            return ParsedCommand(
                intent="query_schedule",
                user_command=command,
                date=self._resolve_date(command, current).isoformat(),
            )
        if self._is_recurring(command):
            return self._parse_recurring(command, current)
        if self._is_update(command):
            return self._parse_update(command, current)
        if self._is_delete(command):
            return self._parse_delete(command, current)
        if self._is_complete(command):
            return self._parse_complete(command)
        if self._is_create(command):
            return self._parse_create(command, current)
        return ParsedCommand(
            intent="unknown",
            user_command=command,
            clarification="我还不能识别这条指令。请尝试：明天下午3点提醒我写周报。",
        )

    def _parse_create(self, command: str, current: datetime) -> ParsedCommand:
        resolved_time = self._resolve_datetime(command, current)
        title = self._clean_title(command, remove_words=["提醒我", "提醒", "创建", "新建", "添加"])
        if not title:
            return ParsedCommand(
                intent="create_task",
                user_command=command,
                clarification="请告诉我要提醒你的任务内容。",
            )
        if not resolved_time:
            return ParsedCommand(
                intent="create_task",
                user_command=command,
                title=title,
                clarification="请告诉我具体日期和时间，例如：明天下午3点。",
            )
        return ParsedCommand(
            intent="create_task",
            user_command=command,
            title=title,
            start_time=resolved_time.isoformat(),
            reminder_time=resolved_time.isoformat(),
        )

    def _parse_update(self, command: str, current: datetime) -> ParsedCommand:
        match = re.search(r"把(.+?)改到(.+)", command)
        query = match.group(1).strip() if match else self._clean_title(command, remove_words=["改到", "修改"])
        resolved_time = self._resolve_datetime(command, current)
        if not query:
            return ParsedCommand(
                intent="update_task",
                user_command=command,
                clarification="请告诉我要修改哪一个任务。",
            )
        if not resolved_time:
            return ParsedCommand(
                intent="update_task",
                user_command=command,
                query=query,
                clarification="请告诉我新的日期和时间。",
            )
        return ParsedCommand(
            intent="update_task",
            user_command=command,
            query=query,
            changes={
                "start_time": resolved_time.isoformat(),
                "reminder_time": resolved_time.isoformat(),
            },
        )

    def _parse_delete(self, command: str, current: datetime) -> ParsedCommand:
        resolved_date = self._resolve_date(command, current)
        query = self._clean_title(command, remove_words=["取消", "删除", "移除"])
        if not query:
            return ParsedCommand(
                intent="delete_task",
                user_command=command,
                clarification="请告诉我要删除哪一个任务。",
            )
        return ParsedCommand(
            intent="delete_task",
            user_command=command,
            query=query,
            date=resolved_date.isoformat(),
        )

    def _parse_complete(self, command: str) -> ParsedCommand:
        query = command
        for word in ("已经完成了", "完成了", "已完成", "做完了", "结束了"):
            query = query.replace(word, "")
        query = query.strip(" ，。,.")
        if not query:
            return ParsedCommand(
                intent="complete_task",
                user_command=command,
                clarification="请告诉我完成的是哪一个任务。",
            )
        return ParsedCommand(intent="complete_task", user_command=command, query=query)

    def _parse_recurring(self, command: str, current: datetime) -> ParsedCommand:
        resolved_time = self._resolve_datetime(command, current, allow_missing_date=True)
        recurring_rule = self._resolve_recurring_rule(command)
        title = self._clean_title(command, remove_words=["每天", "每日", "每周", "提醒我", "提醒"])
        if not title:
            return ParsedCommand(
                intent="set_recurring_task",
                user_command=command,
                clarification="请告诉我重复任务的内容。",
            )
        if not resolved_time:
            return ParsedCommand(
                intent="set_recurring_task",
                user_command=command,
                title=title,
                recurring_rule=recurring_rule,
                clarification="请告诉我重复任务的具体时间。",
            )
        return ParsedCommand(
            intent="set_recurring_task",
            user_command=command,
            title=title,
            start_time=resolved_time.isoformat(),
            reminder_time=resolved_time.isoformat(),
            recurring_rule=recurring_rule,
        )

    def _resolve_date(self, command: str, current: datetime) -> date:
        today = current.date()
        match = DATE_PATTERN.search(command)
        if not match:
            return today
        token = match.group(1)
        if token == "今天":
            return today
        if token == "明天":
            return today + timedelta(days=1)
        if token == "后天":
            return today + timedelta(days=2)
        if token == "昨天":
            return today - timedelta(days=1)
        if token.startswith("本周"):
            target = WEEKDAYS[token[-1]]
            return today + timedelta(days=target - today.weekday())
        if token.startswith("下周"):
            target = WEEKDAYS[token[-1]]
            return today + timedelta(days=(7 - today.weekday()) + target)
        if token.startswith("周"):
            target = WEEKDAYS[token[-1]]
            delta = target - today.weekday()
            if delta < 0:
                delta += 7
            return today + timedelta(days=delta)
        return today

    def _resolve_datetime(
        self,
        command: str,
        current: datetime,
        *,
        allow_missing_date: bool = False,
    ) -> Optional[datetime]:
        parsed_time = self._resolve_time(command)
        if not parsed_time:
            return None
        has_date = DATE_PATTERN.search(command) is not None
        if not has_date and not allow_missing_date:
            return None
        day = self._resolve_date(command, current)
        return datetime.combine(day, parsed_time, tzinfo=self.timezone)

    def _resolve_time(self, command: str) -> Optional[time]:
        match = TIME_PATTERN.search(command)
        if not match:
            return None
        period, hour_text, minute_text, point_suffix = match.groups()
        hour = int(hour_text)
        minute = self._resolve_minute(minute_text, point_suffix)
        if period in {"下午", "晚上"} and hour < 12:
            hour += 12
        if period == "中午" and hour < 11:
            hour += 12
        if hour > 23 or minute > 59:
            return None
        return time(hour=hour, minute=minute)

    def _resolve_minute(self, minute_text: Optional[str], point_suffix: Optional[str]) -> int:
        if minute_text:
            return int(minute_text)
        if point_suffix == "半":
            return 30
        if point_suffix and point_suffix.endswith("分"):
            return int(point_suffix[:-1])
        if point_suffix and point_suffix.isdigit():
            return int(point_suffix)
        return 0

    def _resolve_recurring_rule(self, command: str) -> str:
        if "每天" in command or "每日" in command:
            return "FREQ=DAILY;INTERVAL=1"
        match = re.search(r"每周([一二三四五六日天])", command)
        if match:
            return f"FREQ=WEEKLY;INTERVAL=1;BYDAY={BYDAY[match.group(1)]}"
        return "FREQ=DAILY;INTERVAL=1"

    def _clean_title(self, command: str, *, remove_words: list[str]) -> str:
        title = re.sub(r"每周[一二三四五六日天]", "", command)
        title = DATE_PATTERN.sub("", title)
        title = TIME_PATTERN.sub("", title)
        for word in remove_words:
            title = title.replace(word, "")
        title = re.sub(r"^(把|请|帮我|我想|我要)", "", title)
        title = re.sub(r"(凌晨|早上|上午|中午|下午|晚上)", "", title)
        title = re.sub(r"(到|在)$", "", title)
        return title.strip(" ，。,.")

    def _is_create(self, command: str) -> bool:
        return any(word in command for word in ("提醒我", "提醒", "创建", "新建", "添加"))

    def _is_update(self, command: str) -> bool:
        return "改到" in command or "修改" in command

    def _is_delete(self, command: str) -> bool:
        return any(word in command for word in ("取消", "删除", "移除"))

    def _is_complete(self, command: str) -> bool:
        return any(word in command for word in ("完成了", "已完成", "做完了", "结束了"))

    def _is_query(self, command: str) -> bool:
        return any(word in command for word in ("有什么安排", "日程", "安排", "计划")) and not self._is_create(command)

    def _is_daily_summary(self, command: str) -> bool:
        return "总结" in command or "回顾" in command

    def _is_reminder_check(self, command: str) -> bool:
        return "检查提醒" in command or "扫描提醒" in command

    def _is_recurring(self, command: str) -> bool:
        return "每天" in command or "每日" in command or "每周" in command
