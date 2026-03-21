"""LMS Telegram Bot entry point.

Supports two modes:
1. Test mode: `python bot.py --test "/command"` - prints response to stdout
2. Telegram mode: connects to Telegram API and handles messages
"""

import argparse
import asyncio
import sys
from typing import Any

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from config import config
from handlers import (
    handle_start,
    handle_help,
    handle_health,
    handle_labs,
    handle_scores,
)


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
    
    # Natural language handling - route to appropriate handler
    text_lower = text.lower()
    if "start" in text_lower or "привет" in text_lower or "hello" in text_lower:
        return "start", None
    elif "help" in text_lower or "справк" in text_lower or "команд" in text_lower:
        return "help", None
    elif "health" in text_lower or "статус" in text_lower or "работает" in text_lower:
        return "health", None
    elif "lab" in text_lower or "лаборатор" in text_lower:
        if "score" in text_lower or "оценк" in text_lower:
            # Extract lab name from natural language
            for word in text.split():
                if word.lower().startswith("lab"):
                    return "scores", word
            return "labs", None
        return "labs", None
    elif "score" in text_lower or "оценк" in text_lower:
        # Try to extract lab name
        for word in text.split():
            if word.lower().startswith("lab"):
                return "scores", word
        return "scores", None
    
    return "help", None


def run_test_mode(command: str) -> None:
    """Run bot in test mode - call handler directly and print result.
    
    Args:
        command: Command text to process (e.g., "/start" or "/scores lab-04").
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
    else:
        result = handle_help()
    
    # Print result to stdout
    print(result["text"])
    sys.exit(0)


# Telegram bot handlers
async def cmd_start(message: Message) -> None:
    """Handle /start command from Telegram."""
    result = handle_start(user_id=str(message.from_user.id))
    await message.answer(result["text"])


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
    elif cmd_name == "help":
        result = handle_help(user_id=str(message.from_user.id))
    elif cmd_name == "health":
        result = handle_health(user_id=str(message.from_user.id))
    elif cmd_name == "labs":
        result = handle_labs(user_id=str(message.from_user.id))
    elif cmd_name == "scores":
        result = handle_scores(user_id=str(message.from_user.id), lab_name=arg)
    else:
        result = handle_help(user_id=str(message.from_user.id))
    
    await message.answer(result["text"])


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
