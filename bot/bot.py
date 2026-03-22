"""LMS Telegram Bot entry point.

Supports two modes:
1. Test mode: `python bot.py --test "question"` - prints response to stdout
2. Telegram mode: connects to Telegram API and handles messages
"""

import argparse
import asyncio
import sys
from typing import Any

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import config
from handlers import (
    handle_start,
    handle_help,
    handle_health,
    handle_labs,
    handle_scores,
    handle_natural_language_sync,
)


def create_main_keyboard() -> InlineKeyboardMarkup:
    """Create inline keyboard with common actions.

    Returns:
        Inline keyboard markup with buttons for common queries.
    """
    builder = InlineKeyboardBuilder()

    # Main action buttons
    builder.button(text="📚 Лабораторные", callback_data="labs")
    builder.button(text="📊 Оценки", callback_data="scores_help")
    builder.button(text="🏆 Топ студентов", callback_data="top_help")
    builder.button(text="📈 Статистика", callback_data="stats_help")

    # Help buttons
    builder.button(text="❓ Справка", callback_data="help")
    builder.button(text="🔍 Проверка статуса", callback_data="health")

    builder.adjust(2, 2, 2)  # 2 buttons per row
    return builder.as_markup()


def create_scores_keyboard(lab_id: str) -> InlineKeyboardMarkup:
    """Create inline keyboard for lab-specific actions.

    Args:
        lab_id: Lab identifier.

    Returns:
        Inline keyboard markup with lab-specific buttons.
    """
    builder = InlineKeyboardBuilder()

    builder.button(text="📊 Оценки", callback_data=f"scores_{lab_id}")
    builder.button(text="📈 Проходные баллы", callback_data=f"pass_{lab_id}")
    builder.button(text="🏆 Топ студентов", callback_data=f"top_{lab_id}")
    builder.button(text="👥 Группы", callback_data=f"groups_{lab_id}")
    builder.button(text="📅 Timeline", callback_data=f"timeline_{lab_id}")

    builder.adjust(2, 2, 1)
    return builder.as_markup()


def parse_command(text: str) -> tuple[str, str | None]:
    """Parse command text into command name and arguments.

    Args:
        text: Message text (e.g., "/scores lab-04" or "what labs are available").

    Returns:
        Tuple of (command_name, argument).
    """
    text = text.strip()

    # Check for command format (/command or /command arg)
    if text.startswith("/"):
        parts = text[1:].split(maxsplit=1)
        command = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None
        return command, arg

    # Natural language - return special marker for LLM routing
    return "natural", text


def run_test_mode(command: str) -> None:
    """Run bot in test mode - call handler directly and print result.

    Args:
        command: Command text to process (e.g., "/start" or "which lab has lowest pass rate").
    """
    cmd_name, arg = parse_command(command)

    # Route to appropriate handler
    if cmd_name == "start":
        result = handle_start()
    elif cmd_name == "help":
        result = handle_help()
    elif cmd_name == "health":
        result = handle_health()
    elif cmd_name == "labs":
        result = handle_labs()
    elif cmd_name == "scores":
        result = handle_scores(lab_name=arg)
    elif cmd_name == "natural":
        # Natural language routing via LLM
        result = handle_natural_language_sync(arg)
    else:
        # Default to natural language processing
        result = handle_natural_language_sync(command)

    # Print result to stdout
    print(result["text"])
    sys.exit(0)


# Telegram bot handlers
async def cmd_start(message: Message) -> None:
    """Handle /start command from Telegram."""
    result = handle_start(user_id=str(message.from_user.id))
    await message.answer(result["text"], reply_markup=create_main_keyboard())


async def cmd_help(message: Message) -> None:
    """Handle /help command from Telegram."""
    result = handle_help(user_id=str(message.from_user.id))
    await message.answer(result["text"])


async def cmd_health(message: Message) -> None:
    """Handle /health command from Telegram."""
    result = handle_health(user_id=str(message.from_user.id))
    await message.answer(result["text"])


async def cmd_labs(message: Message) -> None:
    """Handle /labs command from Telegram."""
    result = handle_labs(user_id=str(message.from_user.id))
    await message.answer(result["text"])


async def cmd_scores(message: Message) -> None:
    """Handle /scores command from Telegram."""
    # Extract lab name from command arguments
    lab_name = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    result = handle_scores(user_id=str(message.from_user.id), lab_name=lab_name)
    await message.answer(result["text"])


async def handle_message(message: Message) -> None:
    """Handle natural language messages from users."""
    text = message.text or ""
    cmd_name, arg = parse_command(text)

    # Route to appropriate handler based on intent
    if cmd_name == "start":
        result = handle_start(user_id=str(message.from_user.id))
        await message.answer(result["text"], reply_markup=create_main_keyboard())
    elif cmd_name == "help":
        result = handle_help(user_id=str(message.from_user.id))
        await message.answer(result["text"])
    elif cmd_name == "health":
        result = handle_health(user_id=str(message.from_user.id))
        await message.answer(result["text"])
    elif cmd_name == "labs":
        result = handle_labs(user_id=str(message.from_user.id))
        await message.answer(result["text"])
    elif cmd_name == "scores":
        result = handle_scores(user_id=str(message.from_user.id), lab_name=arg)
        await message.answer(result["text"])
    elif cmd_name == "natural":
        # Natural language processing via LLM intent router
        result = await handle_natural_language(arg, user_id=str(message.from_user.id))
        await message.answer(result["text"])
    else:
        # Fallback to natural language processing
        result = await handle_natural_language(text, user_id=str(message.from_user.id))
        await message.answer(result["text"])


async def handle_callback_query(callback_query: types.CallbackQuery) -> None:
    """Handle inline keyboard button callbacks.

    Args:
        callback_query: Callback query from inline button press.
    """
    data = callback_query.data

    if data == "labs":
        result = handle_labs(user_id=str(callback_query.from_user.id))
        await callback_query.message.answer(result["text"])
    elif data == "scores_help":
        result = handle_help(user_id=str(callback_query.from_user.id))
        await callback_query.message.answer(
            "Для просмотра оценок напишите номер лаборатории, например: lab-01\n"
            "Или выберите лабораторную из списка /labs"
        )
    elif data == "top_help":
        await callback_query.message.answer(
            "Для просмотра топ студентов напишите:\n"
            "«топ 5 студентов в lab-01»\n"
            "Или «top 10 lab-03»"
        )
    elif data == "stats_help":
        await callback_query.message.answer(
            "Я могу показать:\n"
            "• Распределение оценок\n"
            "• Проходные баллы по задачам\n"
            "• Статистику по группам\n"
            "• Timeline сдачи работ\n\n"
            "Просто спросите меня!"
        )
    elif data == "help":
        result = handle_help(user_id=str(callback_query.from_user.id))
        await callback_query.message.answer(result["text"])
    elif data == "health":
        result = handle_health(user_id=str(callback_query.from_user.id))
        await callback_query.message.answer(result["text"])
    else:
        # Handle lab-specific callbacks
        await callback_query.message.answer(f"Обработка запроса: {data}")

    await callback_query.answer()


async def run_telegram_mode() -> None:
    """Run bot in Telegram mode - connect to Telegram API."""
    if not config.bot_token:
        print("Error: BOT_TOKEN not found in .env.bot.secret", file=sys.stderr)
        sys.exit(1)

    bot = Bot(token=config.bot_token)
    dp = Dispatcher()

    # Register handlers
    dp.message.register(cmd_start, CommandStart())
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_health, Command("health"))
    dp.message.register(cmd_labs, Command("labs"))
    dp.message.register(cmd_scores, Command("scores"))
    dp.message.register(handle_message)  # Fallback for natural language

    # Register callback query handler for inline buttons
    dp.callback_query.register(handle_callback_query)

    # Start polling
    print("Bot started...")
    await dp.start_polling(bot)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="LMS Telegram Bot")
    parser.add_argument(
        "--test",
        type=str,
        metavar="COMMAND",
        help="Run in test mode with the specified command",
    )

    args = parser.parse_args()

    if args.test:
        run_test_mode(args.test)
    else:
        asyncio.run(run_telegram_mode())


if __name__ == "__main__":
    main()
