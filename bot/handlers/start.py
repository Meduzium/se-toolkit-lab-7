"""Handler for /start command."""

from .base import create_result


def handle_start(user_id: str | None = None, **kwargs) -> dict:
    """Handle /start command.
    
    Args:
        user_id: Telegram user ID (optional, not used in test mode).
        **kwargs: Additional context (for future extensibility).
    
    Returns:
        Handler result with welcome message.
    """
    text = (
        "👋 Добро пожаловать в LMS Bot!\n\n"
        "Я помогу вам получить информацию о ваших лабораторных работах и оценках.\n\n"
        "Доступные команды:\n"
        "/help — показать список команд\n"
        "/labs — показать доступные лабораторные работы\n"
        "/scores <lab> — показать оценки за лабораторную\n"
        "/health — проверить статус системы\n\n"
        "Вы также можете задавать вопросы естественным языком, например:\n"
        "«какие лабораторные доступны?» или «покажи мои оценки»"
    )
    return create_result(text)
