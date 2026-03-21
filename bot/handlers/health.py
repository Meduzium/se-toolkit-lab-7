"""Handler for /health command."""

from .base import create_result


def handle_health(user_id: str | None = None, **kwargs) -> dict:
    """Handle /health command.
    
    Args:
        user_id: Telegram user ID (optional).
        **kwargs: Additional context.
    
    Returns:
        Handler result with system health status.
    """
    # TODO: Implement real health check with backend API
    text = (
        "✅ Система работает нормально\n\n"
        "Статус компонентов:\n"
        "• Бот: работает\n"
        "• LMS API: ожидание подключения\n"
        "• LLM API: ожидание подключения\n\n"
        "Версия: 0.1.0"
    )
    return create_result(text)
