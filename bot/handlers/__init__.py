"""Command handlers for the LMS bot.

Handlers are pure functions that take input and return text.
They have no knowledge of Telegram - this enables testable architecture.
"""

from .start import handle_start
from .help import handle_help
from .health import handle_health
from .labs import handle_labs
from .scores import handle_scores
from .natural_language import handle_natural_language, handle_natural_language_sync

__all__ = [
    "handle_start",
    "handle_help",
    "handle_health",
    "handle_labs",
    "handle_scores",
    "handle_natural_language",
    "handle_natural_language_sync",
]
