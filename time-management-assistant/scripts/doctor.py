import shutil
import socket
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from db_tunnel import ENV_PATH, load_env


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = PROJECT_ROOT / "backend"
PYTHON = PROJECT_ROOT.parent / ".venv" / "bin" / "python"
DOMAIN = "gui"
SERVICES = {
    "db-tunnel": "com.horris.time-management-assistant.db-tunnel",
    "scheduler": "com.horris.time-management-assistant.scheduler",
}


class CheckResult:
    def __init__(self) -> None:
        self.failed = False

    def ok(self, message: str) -> None:
        print(f"OK   {message}")

    def warn(self, message: str) -> None:
        print(f"WARN {message}")

    def fail(self, message: str) -> None:
        self.failed = True
        print(f"FAIL {message}")


def bool_enabled(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def mask_database_url(value: str) -> str:
    try:
        parts = urlsplit(value)
    except ValueError:
        return value
    if not parts.password:
        return value
    username = parts.username or ""
    host = parts.hostname or ""
    port = f":{parts.port}" if parts.port else ""
    netloc = f"{username}:***@{host}{port}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def safe_error(message: str, config: dict[str, str]) -> str:
    sanitized = message
    secrets = [
        config.get("DATABASE_URL", ""),
        mask_database_url(config.get("DATABASE_URL", "")),
        config.get("SSH_TUNNEL_PASSWORD", ""),
        config.get("BARK_DEVICE_KEY", ""),
    ]
    for secret in secrets:
        if secret:
            sanitized = sanitized.replace(secret, "***")
    return sanitized


def check_env(result: CheckResult, config: dict[str, str]) -> None:
    if ENV_PATH.exists():
        result.ok(f"env file exists: {ENV_PATH}")
    else:
        result.fail(f"env file missing: {ENV_PATH}")
        return

    if config.get("DATABASE_URL"):
        result.ok("DATABASE_URL is configured")
    else:
        result.fail("DATABASE_URL is missing")


def check_tunnel(result: CheckResult, config: dict[str, str]) -> None:
    host = config.get("SSH_TUNNEL_LOCAL_HOST", "127.0.0.1")
    port = int(config.get("SSH_TUNNEL_LOCAL_PORT", "5432"))
    try:
        with socket.create_connection((host, port), timeout=2):
            result.ok(f"local database tunnel is reachable at {host}:{port}")
    except OSError as exc:
        result.warn(f"local database tunnel is not reachable at {host}:{port}: {exc}")


def check_database(result: CheckResult, config: dict[str, str]) -> None:
    database_url = config.get("DATABASE_URL", "")
    if not database_url:
        return

    sys.path.insert(0, str(BACKEND_DIR))
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(database_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})
        with engine.connect() as connection:
            connection.execute(text("select 1"))
        result.ok("PostgreSQL connection succeeded")
    except Exception as exc:
        message = safe_error(str(exc), config)
        result.warn(f"PostgreSQL connection failed: {exc.__class__.__name__}: {message}")


def check_notifications(result: CheckResult, config: dict[str, str]) -> None:
    enabled = bool_enabled(config.get("NOTIFICATION_ENABLED"))
    channels = [
        item.strip().lower()
        for item in config.get("NOTIFICATION_CHANNELS", "bark").split(",")
        if item.strip()
    ]
    state = "enabled" if enabled else "disabled"
    result.ok(f"notifications are {state}; channels={','.join(channels) or 'none'}")

    if not enabled:
        return

    if "bark" in channels:
        if config.get("BARK_DEVICE_KEY"):
            result.ok("Bark device key is configured")
        else:
            result.warn("Bark channel is enabled but BARK_DEVICE_KEY is missing")

    if "wechat_work" in channels:
        if config.get("CC_CONNECT_PROJECT"):
            result.ok("cc-connect project is configured")
        else:
            result.warn("wechat_work channel is enabled but CC_CONNECT_PROJECT is missing")

        command = config.get("CC_CONNECT_COMMAND", "cc-connect")
        if shutil.which(command):
            result.ok(f"cc-connect command is available: {command}")
        else:
            result.warn(f"cc-connect command is not on PATH: {command}")


def check_scheduler_import(result: CheckResult) -> None:
    target = PROJECT_ROOT / "scheduler" / "worker.py"
    python = str(PYTHON if PYTHON.exists() else Path(sys.executable))
    completed = subprocess.run(
        [python, "-m", "py_compile", str(target)],
        text=True,
        capture_output=True,
    )
    if completed.returncode == 0:
        result.ok("scheduler worker compiles")
    else:
        output = (completed.stderr or completed.stdout).strip()
        result.fail(f"scheduler worker compile failed: {output}")


def check_launchd(result: CheckResult) -> None:
    if sys.platform != "darwin":
        result.warn("launchd checks are skipped outside macOS")
        return
    uid = subprocess.run(["id", "-u"], text=True, capture_output=True)
    if uid.returncode != 0:
        result.warn("launchd checks skipped: cannot read user id")
        return
    domain = f"{DOMAIN}/{uid.stdout.strip()}"
    for name, label in SERVICES.items():
        completed = subprocess.run(
            ["launchctl", "print", f"{domain}/{label}"],
            text=True,
            capture_output=True,
        )
        if completed.returncode == 0:
            result.ok(f"launchd service loaded: {name}")
        else:
            result.warn(f"launchd service not loaded: {name}")


def main() -> int:
    config = load_env(ENV_PATH)
    result = CheckResult()

    check_env(result, config)
    check_tunnel(result, config)
    check_database(result, config)
    check_notifications(result, config)
    check_scheduler_import(result)
    check_launchd(result)

    return 1 if result.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
