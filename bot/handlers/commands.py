from __future__ import annotations

from collections.abc import Callable

from config import load_settings
from handlers.shared.messages import WELCOME_MESSAGE
from services.api_client import BackendClient, BackendServiceError

Handler = Callable[[list[str]], str]


def handle_start(_: list[str]) -> str:
    return WELCOME_MESSAGE


def handle_help(_: list[str]) -> str:
    return "\n".join(
        [
            "Available commands:",
            "/start - show a welcome message",
            "/help - list available commands",
            "/health - check backend connectivity",
            "/labs - list labs from the LMS backend",
            "/scores <lab> - show pass rates for a lab",
        ]
    )


def handle_health(_: list[str], client: BackendClient) -> str:
    try:
        items = client.get_items()
    except BackendServiceError as exc:
        return str(exc)

    return f"Backend is healthy. {len(items)} items available."


def handle_labs(_: list[str], client: BackendClient) -> str:
    try:
        items = client.get_items()
    except BackendServiceError as exc:
        return str(exc)

    labs = [item["title"] for item in items if item.get("type") == "lab"]
    if not labs:
        return "No labs found in the backend data."

    lines = ["Available labs:"]
    lines.extend(f"- {title}" for title in labs)
    return "\n".join(lines)


def handle_scores(args: list[str], client: BackendClient) -> str:
    if not args:
        return "Usage: /scores <lab>"

    lab = args[0]
    try:
        pass_rates = client.get_pass_rates(lab)
    except BackendServiceError as exc:
        return str(exc)

    if not pass_rates:
        return f"No pass-rate data found for {lab}."

    lines = [f"Pass rates for {lab}:"]
    lines.extend(
        f"- {item['task']}: {item['avg_score']}% ({item['attempts']} attempts)"
        for item in pass_rates
    )
    return "\n".join(lines)


def build_handlers() -> dict[str, Handler]:
    settings = load_settings()
    base_url = settings.lms_api_base_url
    api_key = settings.lms_api_key
    client = BackendClient(base_url=base_url, api_key=api_key or "")

    return {
        "/start": handle_start,
        "/help": handle_help,
        "/health": lambda args: handle_health(args, client),
        "/labs": lambda args: handle_labs(args, client),
        "/scores": lambda args: handle_scores(args, client),
    }
