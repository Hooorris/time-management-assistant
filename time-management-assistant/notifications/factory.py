import os
from collections.abc import Mapping
from dataclasses import dataclass

from notifications.bark import BarkNotifier
from notifications.base import NotificationMessage, NotificationResult, Notifier
from notifications.cc_connect import CCConnectNotifier


def parse_bool(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_channels(value: str | None, *, default: list[str] | None = None) -> list[str]:
    if not value:
        return list(default or [])
    channels = [item.strip().lower() for item in value.split(",") if item.strip()]
    return channels or list(default or [])


@dataclass(frozen=True)
class NotificationSettings:
    enabled: bool
    channels: list[str]
    bark_server_url: str
    bark_device_key: str
    bark_sound: str | None
    bark_group: str | None
    cc_connect_project: str
    cc_connect_command: str
    cc_connect_timeout_seconds: float


class DryRunNotifier:
    def send(self, message: NotificationMessage) -> NotificationResult:
        return NotificationResult(success=True, channel=message.channel)


class CompositeNotifier:
    def __init__(self, notifiers: list[Notifier]) -> None:
        self.notifiers = {
            getattr(notifier, "channel", ""): notifier
            for notifier in notifiers
            if getattr(notifier, "channel", "")
        }

    def send(self, message: NotificationMessage) -> NotificationResult:
        notifier = self.notifiers.get(message.channel)
        if not notifier:
            return NotificationResult(
                success=False,
                channel=message.channel,
                error_message=f"No notifier configured for channel: {message.channel}",
            )
        return notifier.send(message)


def load_notification_settings(env: Mapping[str, str] | None = None) -> NotificationSettings:
    source = env or os.environ
    return NotificationSettings(
        enabled=parse_bool(source.get("NOTIFICATION_ENABLED"), default=False),
        channels=parse_channels(source.get("NOTIFICATION_CHANNELS"), default=["bark"]),
        bark_server_url=source.get("BARK_SERVER_URL", "https://api.day.app"),
        bark_device_key=source.get("BARK_DEVICE_KEY", ""),
        bark_sound=source.get("BARK_SOUND") or "bell",
        bark_group=source.get("BARK_GROUP") or "Time Management Assistant",
        cc_connect_project=source.get("CC_CONNECT_PROJECT", "my-project"),
        cc_connect_command=source.get("CC_CONNECT_COMMAND", "cc-connect"),
        cc_connect_timeout_seconds=float(source.get("CC_CONNECT_TIMEOUT_SECONDS", "30")),
    )


def create_notifier_from_env(env: Mapping[str, str] | None = None) -> Notifier:
    settings = load_notification_settings(env)
    if not settings.enabled:
        return DryRunNotifier()

    notifiers: list[Notifier] = []
    if "bark" in settings.channels and settings.bark_device_key:
        notifiers.append(
            BarkNotifier(
                server_url=settings.bark_server_url,
                device_key=settings.bark_device_key,
                sound=settings.bark_sound,
                group=settings.bark_group,
            )
        )
    if "wechat_work" in settings.channels:
        notifiers.append(
            CCConnectNotifier(
                project=settings.cc_connect_project,
                command=settings.cc_connect_command,
                timeout_seconds=settings.cc_connect_timeout_seconds,
            )
        )
    return CompositeNotifier(notifiers)
