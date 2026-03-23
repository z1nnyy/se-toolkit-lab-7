from __future__ import annotations

from collections.abc import Callable


Handler = Callable[[list[str]], str]


def handle_start(_: list[str]) -> str:
    return "Welcome to the LMS bot."


def handle_help(_: list[str]) -> str:
    return "\n".join(
        [
            "Available commands:",
            "/start",
            "/help",
            "/health",
            "/labs",
            "/scores <lab>",
        ]
    )


def handle_health(_: list[str]) -> str:
    return "Health check is not implemented yet."


def handle_labs(_: list[str]) -> str:
    return "Labs listing is not implemented yet."


def handle_scores(args: list[str]) -> str:
    if not args:
        return "Usage: /scores <lab>"
    return f"Scores for {args[0]} are not implemented yet."


def build_handlers() -> dict[str, Handler]:
    return {
        "/start": handle_start,
        "/help": handle_help,
        "/health": handle_health,
        "/labs": handle_labs,
        "/scores": handle_scores,
    }
