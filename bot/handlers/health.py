"""Handler for /health command."""

import asyncio

import httpx

from config import config
from services.lms_client import LMSClient
from .base import create_result


def handle_health(user_id: str | None = None, **kwargs) -> dict:
    """Handle /health command.

    Args:
        user_id: Telegram user ID (optional).
        **kwargs: Additional context.

    Returns:
        Handler result with system health status.
    """
    return asyncio.run(_check_health_async())


async def _check_health_async() -> dict:
    """Async health check implementation.

    Returns:
        Handler result with health status.
    """
    client = LMSClient(config.lms_api_base_url, config.lms_api_key)

    try:
        items = await client.get_items()
        item_count = len(items) if items else 0
        text = f"✅ Backend is healthy. {item_count} items available."
        return create_result(text)
    except httpx.ConnectError as e:
        error_msg = _format_connect_error(e)
        text = f"❌ Backend error: {error_msg}. Check that the services are running."
        return create_result(text, success=False)
    except httpx.HTTPStatusError as e:
        error_msg = f"HTTP {e.response.status_code} {e.response.reason_phrase}"
        text = f"❌ Backend error: {error_msg}. The backend service may be down."
        return create_result(text, success=False)
    except httpx.HTTPError as e:
        error_msg = str(e) or "unknown error"
        text = f"❌ Backend error: {error_msg}."
        return create_result(text, success=False)
    finally:
        await client.close()


def _format_connect_error(error: httpx.ConnectError) -> str:
    """Format connection error into user-friendly message.

    Args:
        error: The connection error.

    Returns:
        Formatted error message with actual error details.
    """
    error_str = str(error).lower()

    # Check for specific error patterns
    if "connection refused" in error_str:
        if config.lms_api_base_url:
            url = config.lms_api_base_url.replace("http://", "").replace("https://", "")
            return f"connection refused ({url})"
        return "connection refused"
    elif "connection timed out" in error_str or "timed out" in error_str:
        return "connection timed out"
    elif "name resolution" in error_str or "nodename nor servname" in error_str:
        return "DNS resolution failed"
    elif "all connection attempts failed" in error_str:
        # Generic connection failure - include the URL
        if config.lms_api_base_url:
            return f"connection failed ({config.lms_api_base_url})"
        return "all connection attempts failed"
    else:
        # Return the actual error message for debugging
        return str(error)
