"""Handler for /scores command."""

from .base import create_result


def handle_scores(user_id: str | None = None, lab_name: str | None = None, **kwargs) -> dict:
    """Handle /scores command.
    
    Args:
        user_id: Telegram user ID (optional).
        lab_name: Name of the lab to get scores for.
        **kwargs: Additional context.
    
    Returns:
        Handler result with scores information.
    """
    if not lab_name:
        text = (
            "⚠️ Укажите название лабораторной работы.\n\n"
            "Пример использования:\n"
            "/scores lab-04\n\n"
            "Доступные работы: lab-01, lab-02, lab-03, lab-04, lab-05, lab-06, lab-07"
        )
        return create_result(text)
    
    # TODO: Implement real scores lookup from LMS API
    text = (
        f"📊 Оценки за {lab_name}:\n\n"
        f"Статус: в разработке\n"
        "Критерии:\n"
        "• Код: ожидание проверки\n"
        "• Тесты: ожидание проверки\n"
        "• Документация: ожидание проверки\n\n"
        "Общая оценка: будет доступна после проверки"
    )
    return create_result(text)
