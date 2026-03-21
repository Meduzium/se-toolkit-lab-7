"""Handler for /help command."""

from .base import create_result


def handle_help(user_id: str | None = None, **kwargs) -> dict:
    """Handle /help command.
    
    Args:
        user_id: Telegram user ID (optional).
        **kwargs: Additional context.
    
    Returns:
        Handler result with command list.
    """
    text = (
        "📚 Справка по командам бота:\n\n"
        "🔹 /start — приветственное сообщение\n"
        "🔹 /help — эта справка\n"
        "🔹 /labs — список доступных лабораторных работ\n"
        "🔹 /scores <lab_name> — оценки за конкретную лабораторную\n"
        "🔹 /health — проверка статуса системы\n\n"
        "💡 Вы также можете задавать вопросы естественным языком:\n"
        "• «какие лабораторные есть?»\n"
        "• «покажи оценки за lab-01»\n"
        "• «что нужно сделать?»"
    )
    return create_result(text)
