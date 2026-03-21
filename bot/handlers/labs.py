"""Handler for /labs command."""

from .base import create_result


def handle_labs(user_id: str | None = None, **kwargs) -> dict:
    """Handle /labs command.
    
    Args:
        user_id: Telegram user ID (optional).
        **kwargs: Additional context.
    
    Returns:
        Handler result with available labs list.
    """
    # TODO: Implement real labs list from LMS API
    text = (
        "📋 Доступные лабораторные работы:\n\n"
        "• lab-01 — Market, Product & Git\n"
        "• lab-02 — Docker & Containerization\n"
        "• lab-03 — Backend API Development\n"
        "• lab-04 — Frontend Integration\n"
        "• lab-05 — Testing & CI/CD\n"
        "• lab-06 — Deployment & Monitoring\n"
        "• lab-07 — LLM Integration\n\n"
        "Используйте /scores <lab_name> для просмотра оценок.\n"
        "Например: /scores lab-04"
    )
    return create_result(text)
