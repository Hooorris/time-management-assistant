import logging
import os
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv  # noqa: E402

from app.database import get_session_local  # noqa: E402
from app.services import TaskService  # noqa: E402
from notifications import NotificationMessage, Notifier, create_notifier_from_env  # noqa: E402


load_dotenv(BACKEND_ROOT / ".env")

logger = logging.getLogger("time_management_scheduler")
shutdown_requested = False


def configure_logging() -> None:
    logging.basicConfig(
        level=os.getenv("SCHEDULER_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def parse_bool(value: Optional[str], *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_channels(value: Optional[str]) -> Optional[list[str]]:
    if not value:
        return None
    channels = [item.strip().lower() for item in value.split(",") if item.strip()]
    return channels or None


def request_shutdown(signum, frame) -> None:
    global shutdown_requested
    shutdown_requested = True
    logger.info("Shutdown requested by signal %s", signum)


def build_notification_message(reminder: dict) -> NotificationMessage:
    task = reminder.get("task") or {}
    title = task.get("title") or "Time Management Assistant"
    send_time = reminder.get("send_time")
    body = task.get("description") or f"Reminder due at {send_time}"
    return NotificationMessage(
        channel=reminder.get("channel", ""),
        title=title,
        body=body,
        metadata={
            "reminder_id": reminder.get("id"),
            "task_id": reminder.get("task_id"),
            "send_time": send_time,
        },
    )


def run_once(*, channels: Optional[list[str]] = None, notifier: Optional[Notifier] = None) -> dict:
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        service = TaskService(db)
        scan_time = datetime.now(timezone.utc)
        notifier = notifier or create_notifier_from_env()
        result = service.list_due_reminders(now=scan_time, channels=channels)
        processed_reminders = []
        sent_count = 0
        failed_count = 0

        for reminder in result["reminders"]:
            logger.info(
                "Reminder due: task_id=%s reminder_id=%s channel=%s send_time=%s",
                reminder.get("task_id"),
                reminder.get("id"),
                reminder.get("channel"),
                reminder.get("send_time"),
            )
            send_result = notifier.send(build_notification_message(reminder))
            if send_result.success:
                marked = service.mark_reminder_sent(
                    reminder_id=reminder["id"],
                    sent_at=scan_time,
                    user_command="scheduler reminder sent",
                )
                processed_reminder = marked["reminder"]
                sent_count += 1
                logger.info(
                    "Reminder notification sent: task_id=%s reminder_id=%s channel=%s",
                    reminder.get("task_id"),
                    reminder.get("id"),
                    reminder.get("channel"),
                )
            else:
                error_message = send_result.error_message or "Notification failed."
                marked = service.mark_reminder_failed(
                    reminder_id=reminder["id"],
                    error_message=error_message,
                    user_command="scheduler reminder failed",
                )
                processed_reminder = marked["reminder"]
                failed_count += 1
                logger.error(
                    "Reminder notification failed: task_id=%s reminder_id=%s channel=%s error=%s",
                    reminder.get("task_id"),
                    reminder.get("id"),
                    reminder.get("channel"),
                    error_message,
                )
            processed_reminders.append(processed_reminder)

        logger.info(
            "Reminder scan complete: count=%s sent=%s failed=%s",
            result["count"],
            sent_count,
            failed_count,
        )
        return {
            "reminders": processed_reminders,
            "count": len(processed_reminders),
            "sent_count": sent_count,
            "failed_count": failed_count,
        }
    finally:
        db.close()


def main() -> int:
    configure_logging()
    signal.signal(signal.SIGINT, request_shutdown)
    signal.signal(signal.SIGTERM, request_shutdown)

    interval_seconds = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "60"))
    run_once_only = parse_bool(os.getenv("SCHEDULER_RUN_ONCE"), default=False)
    channels = (
        parse_channels(os.getenv("SCHEDULER_CHANNELS"))
        or parse_channels(os.getenv("NOTIFICATION_CHANNELS"))
        or ["bark"]
    )

    logger.info(
        "Starting reminder scheduler: interval_seconds=%s run_once=%s channels=%s",
        interval_seconds,
        run_once_only,
        channels,
    )

    while not shutdown_requested:
        run_once(channels=channels)
        if run_once_only:
            break
        time.sleep(interval_seconds)

    logger.info("Reminder scheduler stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
