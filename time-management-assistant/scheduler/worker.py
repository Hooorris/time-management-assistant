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
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv  # noqa: E402

from app.database import get_session_local  # noqa: E402
from app.services import TaskService  # noqa: E402


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
    channels = [item.strip() for item in value.split(",") if item.strip()]
    return channels or None


def request_shutdown(signum, frame) -> None:
    global shutdown_requested
    shutdown_requested = True
    logger.info("Shutdown requested by signal %s", signum)


def run_once(*, channels: Optional[list[str]] = None) -> dict:
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        service = TaskService(db)
        result = service.check_reminders(
            now=datetime.now(timezone.utc),
            channels=channels,
            user_command="scheduler reminder scan",
        )
        for reminder in result["reminders"]:
            logger.info(
                "Reminder due: task_id=%s reminder_id=%s channel=%s send_time=%s",
                reminder.get("task_id"),
                reminder.get("id"),
                reminder.get("channel"),
                reminder.get("send_time"),
            )
        logger.info("Reminder scan complete: count=%s", result["count"])
        return result
    finally:
        db.close()


def main() -> int:
    configure_logging()
    signal.signal(signal.SIGINT, request_shutdown)
    signal.signal(signal.SIGTERM, request_shutdown)

    interval_seconds = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "60"))
    run_once_only = parse_bool(os.getenv("SCHEDULER_RUN_ONCE"), default=False)
    channels = parse_channels(os.getenv("SCHEDULER_CHANNELS", "telegram"))

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
