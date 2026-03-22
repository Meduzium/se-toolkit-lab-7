"""Handler for natural language queries via LLM intent routing."""

import asyncio
from typing import Any

from services.llm_client import LLMClient
from services.lms_client import LMSClient
from services.intent_router import IntentRouter
from config import config


# Cache for clients (created once per process)
_router: IntentRouter | None = None


def _get_router() -> IntentRouter:
    """Get or create the intent router singleton."""
    global _router
    if _router is not None:
        return _router

    llm_client = LLMClient(
        api_key=config.llm_api_key,
        base_url=config.llm_api_base_url,
        model=config.llm_api_model,
    )

    lms_client = LMSClient(
        base_url=config.lms_api_base_url,
        api_key=config.lms_api_key,
    )

    _router = IntentRouter(llm_client, lms_client)
    return _router


async def handle_natural_language(
    user_message: str,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Handle natural language query using LLM intent routing.

    Args:
        user_message: User's natural language message.
        user_id: Telegram user ID (optional).

    Returns:
        Handler result dictionary with 'text' key.
    """
    router = _get_router()
    response = await router.route(user_message)

    return {"text": response}


def handle_natural_language_sync(
    user_message: str,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Synchronous wrapper for handle_natural_language.

    Args:
        user_message: User's natural language message.
        user_id: Telegram user ID (optional).

    Returns:
        Handler result dictionary with 'text' key.
    """
    return asyncio.run(handle_natural_language(user_message, user_id))


def get_capabilities() -> str:
    """Get bot capabilities text for fallback messages.

    Returns:
        Capabilities description text.
    """
    return _get_router().get_capabilities_text()
