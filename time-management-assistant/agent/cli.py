import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.runner import AgentRunner  # noqa: E402


def run_once(args: argparse.Namespace) -> int:
    runner = AgentRunner(timezone_name=args.timezone)
    command = " ".join(args.command).strip()
    if not command:
        print("请输入指令。")
        return 1
    try:
        if any(word in command for word in ("取消", "删除", "移除")):
            print(runner.handle_delete_with_prompt(command))
        else:
            print(runner.handle_once(command))
        return 0
    except RuntimeError as exc:
        print(f"运行失败：{exc}")
        return 1


def run_chat(args: argparse.Namespace) -> int:
    runner = AgentRunner(timezone_name=args.timezone)
    print("时间管理助手已启动。输入 exit 或 quit 退出。")
    while True:
        try:
            command = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if command.lower() in {"exit", "quit"}:
            return 0
        if not command:
            continue
        try:
            if any(word in command for word in ("取消", "删除", "移除")):
                print(runner.handle_delete_with_prompt(command))
            else:
                print(runner.handle_once(command))
        except RuntimeError as exc:
            print(f"运行失败：{exc}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local Time Management Assistant Agent")
    parser.add_argument("--timezone", default="Asia/Shanghai")
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    once = subparsers.add_parser("once", help="Run one natural-language command")
    once.add_argument("command", nargs=argparse.REMAINDER)
    once.set_defaults(func=run_once)

    chat = subparsers.add_parser("chat", help="Start an interactive chat session")
    chat.set_defaults(func=run_chat)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
