import openai
import pytest

from agent.llm_parser import LLMCommandParser, LLMParserError
from agent.runner import AgentRunner
from agent.schemas import LLMParsedCommand


def test_llm_parser_accepts_structured_parse(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class Message:
        parsed = LLMParsedCommand(
            intent="create_task",
            title="写周报",
            start_time="2026-06-20T15:00:00+08:00",
            reminder_time="2026-06-20T15:00:00+08:00",
        )

    class Choice:
        message = Message()

    class Response:
        choices = [Choice()]

    class Completions:
        def parse(self, **kwargs):
            assert kwargs["response_format"] is LLMParsedCommand
            return Response()

    class Chat:
        completions = Completions()

    class Beta:
        chat = Chat()

    class FakeClient:
        beta = Beta()

    monkeypatch.setattr(openai, "OpenAI", lambda **kwargs: FakeClient())

    parsed = LLMCommandParser().parse("明天下午3点提醒我写周报")

    assert parsed.intent == "create_task"
    assert parsed.title == "写周报"


def test_llm_parser_rejects_empty_parsed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class Message:
        parsed = None

    class Choice:
        message = Message()

    class Response:
        choices = [Choice()]

    class Completions:
        def parse(self, **kwargs):
            return Response()

    class Chat:
        completions = Completions()

    class Beta:
        chat = Chat()

    class FakeClient:
        beta = Beta()

    monkeypatch.setattr(openai, "OpenAI", lambda **kwargs: FakeClient())

    with pytest.raises(LLMParserError):
        LLMCommandParser().parse("今天有什么安排")


def test_auto_parser_falls_back_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    parsed = AgentRunner(parser_mode="auto")._parse_command("今天有什么安排")

    assert parsed.intent == "query_schedule"


def test_llm_mode_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(LLMParserError):
        AgentRunner(parser_mode="llm")._parse_command("今天有什么安排")
