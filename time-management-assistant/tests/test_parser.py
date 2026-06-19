from datetime import datetime
from zoneinfo import ZoneInfo

from agent.parser import ChineseCommandParser


def test_rule_parser_create_task() -> None:
    parser = ChineseCommandParser()
    now = datetime(2026, 6, 19, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    parsed = parser.parse("明天下午3点提醒我写周报", now=now)

    assert parsed.intent == "create_task"
    assert parsed.title == "写周报"
    assert parsed.start_time == "2026-06-20T15:00:00+08:00"


def test_rule_parser_common_intents() -> None:
    parser = ChineseCommandParser()
    now = datetime(2026, 6, 19, 10, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    assert parser.parse("今天有什么安排", now=now).intent == "query_schedule"
    assert parser.parse("把健身改到明天早上8点", now=now).changes["start_time"] == "2026-06-20T08:00:00+08:00"
    assert parser.parse("取消周五下午会议", now=now).query == "会议"
    assert parser.parse("周报完成了", now=now).intent == "complete_task"
    assert parser.parse("每天早上8点学习英语", now=now).recurring_rule == "FREQ=DAILY;INTERVAL=1"
    assert parser.parse("每周一上午9点复盘", now=now).recurring_rule == "FREQ=WEEKLY;INTERVAL=1;BYDAY=MO"
