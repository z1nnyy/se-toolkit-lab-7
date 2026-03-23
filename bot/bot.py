from __future__ import annotations

import argparse
import shlex

from handlers.commands import build_handlers


def run_test_mode(command_text: str) -> int:
    parts = shlex.split(command_text)
    if not parts:
        print("Please provide a command.")
        return 0

    handlers = build_handlers()
    command = parts[0]
    args = parts[1:]
    handler = handlers.get(command)

    if handler is None:
        print(f"Unknown command: {command}. Use /help to see available commands.")
        return 0

    print(handler(args))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", metavar="COMMAND")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.test is not None:
        return run_test_mode(args.test)

    print("Telegram mode is not implemented yet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
