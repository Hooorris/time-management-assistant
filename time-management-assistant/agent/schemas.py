from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from agent.parser import ParsedCommand


IntentName = Literal[
    "create_task",
    "update_task",
    "delete_task",
    "query_schedule",
    "complete_task",
    "set_recurring_task",
    "check_reminders",
    "daily_summary",
    "unknown",
]


class LLMParsedCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: IntentName = Field(description="Canonical command intent.")
    title: Optional[str] = Field(default=None, description="Task title for create or recurring commands.")
    query: Optional[str] = Field(default=None, description="Search keyword for existing task lookup.")
    date: Optional[str] = Field(default=None, description="Local date in YYYY-MM-DD format.")
    start_time: Optional[str] = Field(default=None, description="ISO 8601 start datetime with timezone.")
    reminder_time: Optional[str] = Field(default=None, description="ISO 8601 reminder datetime with timezone.")
    recurring_rule: Optional[str] = Field(default=None, description="RRULE text for recurring tasks.")
    changes: dict[str, Any] = Field(default_factory=dict, description="Task update changes.")
    clarification: Optional[str] = Field(default=None, description="Question to ask when command is ambiguous.")

    def to_parsed_command(self, user_command: str) -> ParsedCommand:
        return ParsedCommand(
            intent=self.intent,
            user_command=user_command,
            title=self.title,
            query=self.query,
            date=self.date,
            start_time=self.start_time,
            reminder_time=self.reminder_time,
            recurring_rule=self.recurring_rule,
            changes=self.changes,
            clarification=self.clarification,
        )
