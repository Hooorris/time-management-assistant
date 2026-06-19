import argparse
import os
import select
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / "backend" / ".env"


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key.strip()] = value
    return values


def require(config: dict[str, str], key: str, default: str | None = None) -> str:
    value = config.get(key, default)
    if value is None or value == "":
        raise SystemExit(f"{key} is required in {ENV_PATH}.")
    return value


def ssh_target(config: dict[str, str]) -> str:
    return f"{require(config, 'SSH_TUNNEL_USER')}@{require(config, 'SSH_TUNNEL_HOST')}"


def ssh_base(config: dict[str, str]) -> list[str]:
    return [
        "ssh",
        "-S",
        require(config, "SSH_TUNNEL_CONTROL_PATH", "/private/tmp/tma-db-tunnel"),
        "-p",
        require(config, "SSH_TUNNEL_PORT", "22"),
    ]


def status(config: dict[str, str]) -> int:
    command = ssh_base(config) + ["-O", "check", ssh_target(config)]
    result = subprocess.run(command, text=True, capture_output=True)
    output = (result.stdout + result.stderr).strip()
    if output:
        print(output)
    return result.returncode


def stop(config: dict[str, str]) -> int:
    command = ssh_base(config) + ["-O", "exit", ssh_target(config)]
    result = subprocess.run(command, text=True, capture_output=True)
    output = (result.stdout + result.stderr).strip()
    if output:
        print(output)
    return result.returncode


def start(config: dict[str, str]) -> int:
    if status(config) == 0:
        return 0

    local_host = require(config, "SSH_TUNNEL_LOCAL_HOST", "127.0.0.1")
    local_port = require(config, "SSH_TUNNEL_LOCAL_PORT", "5432")
    remote_host = require(config, "SSH_TUNNEL_REMOTE_HOST", "127.0.0.1")
    remote_port = require(config, "SSH_TUNNEL_REMOTE_PORT", "5432")
    forward = f"{local_host}:{local_port}:{remote_host}:{remote_port}"
    command = [
        "ssh",
        "-M",
        "-S",
        require(config, "SSH_TUNNEL_CONTROL_PATH", "/private/tmp/tma-db-tunnel"),
        "-fN",
        "-o",
        "ExitOnForwardFailure=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-p",
        require(config, "SSH_TUNNEL_PORT", "22"),
        "-L",
        forward,
        ssh_target(config),
    ]

    password = config.get("SSH_TUNNEL_PASSWORD", "")
    if not password:
        return subprocess.run(command).returncode
    return run_with_password(command, password)


def run_with_password(command: list[str], password: str) -> int:
    master_fd, slave_fd = os.openpty()
    process = subprocess.Popen(
        command,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        close_fds=True,
    )
    os.close(slave_fd)
    sent_password = False
    deadline = time.monotonic() + 45
    output = bytearray()
    try:
        while process.poll() is None:
            if time.monotonic() > deadline:
                process.kill()
                print("SSH tunnel start timed out.", file=sys.stderr)
                return 124
            ready, _, _ = select.select([master_fd], [], [], 0.2)
            if not ready:
                continue
            chunk = os.read(master_fd, 4096)
            output.extend(chunk)
            lowered = bytes(output).lower()
            if not sent_password and b"password:" in lowered:
                os.write(master_fd, (password + "\n").encode())
                sent_password = True
        return process.returncode or 0
    finally:
        os.close(master_fd)


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage the local PostgreSQL SSH tunnel.")
    parser.add_argument("command", choices=("start", "status", "stop"))
    args = parser.parse_args()
    config = load_env(ENV_PATH)
    if args.command == "start":
        return start(config)
    if args.command == "status":
        return status(config)
    return stop(config)


if __name__ == "__main__":
    raise SystemExit(main())
