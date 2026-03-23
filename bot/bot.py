from __future__ import annotations

import argparse
import shlex

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup

from config import load_settings
from handlers.commands import build_handlers
from services.api_client import BackendClient
from services.llm_client import LlmClient, LlmServiceError


def build_quick_actions() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/help"), KeyboardButton(text="/labs")],
            [KeyboardButton(text="/health"), KeyboardButton(text="what labs are available?")],
        ],
        resize_keyboard=True,
    )


def build_llm_client() -> LlmClient:
    settings = load_settings()
    if not settings.llm_api_key:
        raise LlmServiceError("LLM error: LLM_API_KEY is required.")
    if not settings.llm_api_base_url:
        raise LlmServiceError("LLM error: LLM_API_BASE_URL is required.")

    backend_client = BackendClient(
        base_url=settings.lms_api_base_url,
        api_key=settings.lms_api_key or "",
    )
    return LlmClient(
        base_url=settings.llm_api_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_api_model or "qwen3-coder-plus",
        backend_client=backend_client,
    )


def dispatch_text(command_text: str) -> str:
    if command_text.startswith("/"):
        parts = shlex.split(command_text)
        if not parts:
            return "Please provide a command."

        handlers = build_handlers()
        command = parts[0]
        args = parts[1:]
        handler = handlers.get(command)

        if handler is None:
            return f"Unknown command: {command}. Use /help to see available commands."

        return handler(args)

    try:
        return build_llm_client().route(command_text)
    except LlmServiceError as exc:
        return str(exc)


def run_test_mode(command_text: str) -> int:
    print(dispatch_text(command_text))
    return 0


async def run_telegram_mode() -> int:
    settings = load_settings()
    if not settings.bot_token:
        print("BOT_TOKEN is required for Telegram mode.")
        return 1

    bot = Bot(settings.bot_token)
    dispatcher = Dispatcher()

    @dispatcher.message(CommandStart())
    async def handle_start_message(message: Message) -> None:
        await message.answer(
            dispatch_text("/start"),
            reply_markup=build_quick_actions(),
        )

    @dispatcher.message()
    async def handle_text_message(message: Message) -> None:
        text = message.text or ""
        await message.answer(dispatch_text(text), reply_markup=build_quick_actions())

    await dispatcher.start_polling(bot)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", metavar="COMMAND")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.test is not None:
        return run_test_mode(args.test)

    import asyncio

    return asyncio.run(run_telegram_mode())


if __name__ == "__main__":
    raise SystemExit(main())
