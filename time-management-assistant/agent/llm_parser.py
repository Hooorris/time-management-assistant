import os
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from agent.parser import ParsedCommand
from agent.schemas import LLMParsedCommand


SYSTEM_MESSAGE = """You are the parsing layer for a personal time management agent.

Convert the user's Chinese schedule command into one JSON object that matches the provided schema.

Rules:
- Output only structured fields; never execute actions.
- Use only canonical intents from the schema.
- All datetimes must be ISO 8601 with timezone offset.
- Use the provided current time and timezone for relative dates.
- Ask for clarification when task target, date, time, or recurrence is ambiguous.
- For update/delete/complete commands, put task lookup text in query.
- For delete commands, never mark confirmation as complete; the CLI confirms separately.
- For recurring tasks, use RRULE text such as FREQ=DAILY;INTERVAL=1 or FREQ=WEEKLY;INTERVAL=1;BYDAY=MO.
- Do not invent task data. Existing task data can only come from later database queries.
"""


class LLMParserError(RuntimeError):
    pass


class LLMCommandParser:
    def __init__(self, timezone_name: str = "Asia/Shanghai") -> None:
        self.timezone = ZoneInfo(timezone_name)
        self.provider = os.getenv("AGENT_LLM_PROVIDER", "openai")
        self.model = os.getenv("AGENT_LLM_MODEL", "gpt-5-mini")
        self.timeout = float(os.getenv("AGENT_LLM_TIMEOUT_SECONDS", "30"))
        self.temperature = float(os.getenv("AGENT_LLM_TEMPERATURE", "0"))
        self.api_key = os.getenv("OPENAI_API_KEY", "")

    def is_available(self) -> bool:
        return self.provider == "openai" and bool(self.api_key)

    def parse(self, text: str, *, now: Optional[datetime] = None) -> ParsedCommand:
        if self.provider != "openai":
            raise LLMParserError(f"Unsupported LLM provider: {self.provider}")
        if not self.api_key:
            raise LLMParserError("OPENAI_API_KEY is not configured.")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise LLMParserError("openai package is not installed.") from exc

        current = now or datetime.now(self.timezone)
        client = OpenAI(api_key=self.api_key, timeout=self.timeout)
        try:
            response = client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_MESSAGE},
                    {
                        "role": "user",
                        "content": (
                            f"Current time: {current.isoformat()}\n"
                            f"Timezone: {self.timezone.key}\n"
                            f"User command: {text}"
                        ),
                    },
                ],
                temperature=self.temperature,
                response_format=LLMParsedCommand,
            )
        except Exception as exc:
            raise LLMParserError(f"LLM request failed: {exc}") from exc

        parsed = response.choices[0].message.parsed
        if not parsed:
            raise LLMParserError("LLM returned invalid command JSON.")
        return parsed.to_parsed_command(text)
