import argparse
import os
import plistlib
import subprocess
import sys
from pathlib import Path

from db_tunnel import ENV_PATH, load_env


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON = PROJECT_ROOT.parent / ".venv" / "bin" / "python"
LAUNCH_AGENTS_DIR = Path.home() / "Library" / "LaunchAgents"
LOG_DIR = Path.home() / "Library" / "Logs" / "time-management-assistant"
DOMAIN = f"gui/{os.getuid()}"

SERVICES = {
    "db-tunnel": {
        "label": "com.horris.time-management-assistant.db-tunnel",
        "program": [str(PYTHON), str(PROJECT_ROOT / "scripts" / "db_tunnel.py"), "start"],
        "run_at_load": True,
        "start_interval": 60,
    },
    "scheduler": {
        "label": "com.horris.time-management-assistant.scheduler",
        "program": [str(PYTHON), str(PROJECT_ROOT / "scheduler" / "worker.py")],
        "run_at_load": True,
        "keep_alive": True,
        "throttle_interval": 30,
    },
}


def plist_path(service: dict[str, object]) -> Path:
    return LAUNCH_AGENTS_DIR / f"{service['label']}.plist"


def plist_payload(name: str, service: dict[str, object]) -> dict[str, object]:
    label = str(service["label"])
    payload: dict[str, object] = {
        "Label": label,
        "ProgramArguments": service["program"],
        "WorkingDirectory": str(PROJECT_ROOT),
        "RunAtLoad": service.get("run_at_load", False),
        "StandardOutPath": str(LOG_DIR / f"{name}.out.log"),
        "StandardErrorPath": str(LOG_DIR / f"{name}.err.log"),
        "EnvironmentVariables": {
            "PYTHONUNBUFFERED": "1",
        },
    }
    if "start_interval" in service:
        payload["StartInterval"] = service["start_interval"]
    if "keep_alive" in service:
        payload["KeepAlive"] = service["keep_alive"]
    if "throttle_interval" in service:
        payload["ThrottleInterval"] = service["throttle_interval"]
    return payload


def run(command: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=check)


def write_plists() -> None:
    if not PYTHON.exists():
        raise SystemExit(f"Python interpreter not found: {PYTHON}")
    LAUNCH_AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    for name, service in SERVICES.items():
        path = plist_path(service)
        with path.open("wb") as file:
            plistlib.dump(plist_payload(name, service), file, sort_keys=False)
        print(f"wrote {path}")


def notification_enabled() -> bool:
    value = load_env(ENV_PATH).get("NOTIFICATION_ENABLED", "")
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def install(*, allow_dry_run_scheduler: bool = False) -> int:
    if not allow_dry_run_scheduler and not notification_enabled():
        print(
            "NOTIFICATION_ENABLED=true is required before installing launchd services. "
            "Use --allow-dry-run-scheduler only when you intentionally want dry-run scans "
            "to mark due reminders as sent.",
            file=sys.stderr,
        )
        return 2
    write_plists()
    exit_code = 0
    for service in SERVICES.values():
        label = str(service["label"])
        path = plist_path(service)
        run(["launchctl", "bootout", DOMAIN, label])
        result = run(["launchctl", "bootstrap", DOMAIN, str(path)])
        if result.returncode != 0:
            print(result.stderr.strip(), file=sys.stderr)
            exit_code = result.returncode
            continue
        run(["launchctl", "enable", f"{DOMAIN}/{label}"])
        run(["launchctl", "kickstart", "-k", f"{DOMAIN}/{label}"])
        print(f"started {label}")
    return exit_code


def uninstall() -> int:
    for service in SERVICES.values():
        label = str(service["label"])
        run(["launchctl", "bootout", DOMAIN, label])
        path = plist_path(service)
        if path.exists():
            path.unlink()
            print(f"removed {path}")
    return 0


def status() -> int:
    for service in SERVICES.values():
        label = str(service["label"])
        result = run(["launchctl", "print", f"{DOMAIN}/{label}"])
        state = "loaded" if result.returncode == 0 else "not loaded"
        print(f"{label}: {state}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Install or manage local launchd services.")
    parser.add_argument("command", choices=("write", "install", "status", "uninstall"))
    parser.add_argument(
        "--allow-dry-run-scheduler",
        action="store_true",
        help="Allow install when NOTIFICATION_ENABLED is false.",
    )
    args = parser.parse_args()
    if args.command == "write":
        write_plists()
        return 0
    if args.command == "install":
        return install(allow_dry_run_scheduler=args.allow_dry_run_scheduler)
    if args.command == "status":
        return status()
    return uninstall()


if __name__ == "__main__":
    raise SystemExit(main())
