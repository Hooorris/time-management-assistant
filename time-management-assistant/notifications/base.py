from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class NotificationMessage:
    channel: str
    title: str
    body: str
    url: str | None = None
    sound: str | None = None
    group: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NotificationResult:
    success: bool
    channel: str
    error_message: str | None = None
    status_code: int | None = None
    response_body: str | None = None


class Notifier(Protocol):
    def send(self, message: NotificationMessage) -> NotificationResult:
        """Send one notification message."""
