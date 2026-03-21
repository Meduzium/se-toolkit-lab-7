"""Configuration loading from environment variables."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class BotConfig(BaseSettings):
    """Bot configuration loaded from environment variables."""

    # Telegram
    bot_token: str = ""

    # LMS API
    lms_api_base_url: str = "http://localhost:42002"
    lms_api_key: str = ""

    # LLM API
    llm_api_model: str = "openrouter/free"
    llm_api_key: str = ""
    llm_api_base_url: str = "https://openrouter.ai/api/v1"

    class Config:
        env_file = ".env.bot.secret"
        env_file_encoding = "utf-8"


def load_config() -> BotConfig:
    """Load configuration from .env.bot.secret file.
    
    Searches for the file in the bot/ directory or parent directory.
    """
    # Try to find .env.bot.secret in bot/ directory or parent
    script_dir = Path(__file__).parent
    possible_paths = [
        script_dir / ".env.bot.secret",
        script_dir.parent / ".env.bot.secret",
    ]
    
    env_file = None
    for path in possible_paths:
        if path.exists():
            env_file = path
            break
    
    if env_file:
        return BotConfig(_env_file=env_file)
    
    # Fallback to environment variables
    return BotConfig()


config = load_config()
