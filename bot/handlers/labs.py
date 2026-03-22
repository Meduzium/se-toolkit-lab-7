"""Handler for /labs command."""

import asyncio

import httpx

from config import config
from services.lms_client import LMSClient
from .base import create_result


def handle_labs(user_id: str | None = None, **kwargs) -> dict:
    """Handle /labs command.

    Args:
        user_id: Telegram user ID (optional).
        **kwargs: Additional context.

    Returns:
        Handler result with available labs list.
    """
    return asyncio.run(_fetch_labs_async())


async def _fetch_labs_async() -> dict:
    """Async labs fetch implementation.

    Returns:
        Handler result with labs list.
    """
    client = LMSClient(config.lms_api_base_url, config.lms_api_key)

    try:
        items = await client.get_items()

        if not items:
            text = "📋 No labs available at the moment. Please try again later."
            return create_result(text)

        # Filter and format labs
        # Items can be labs or tasks - we need to identify labs
        labs = _extract_labs_from_items(items)

        if not labs:
            text = "📋 No labs found in the backend."
            return create_result(text)

        # Format the response
        lines = ["📚 Available labs:"]
        for lab in labs:
            lab_name = lab.get("name", lab.get("id", "Unknown"))
            lab_title = lab.get("title", "")
            if lab_title:
                lines.append(f"- {lab_name} — {lab_title}")
            else:
                lines.append(f"- {lab_name}")

        text = "\n".join(lines)
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


def _extract_labs_from_items(items: list[dict]) -> list[dict]:
    """Extract lab items from the items list.

    Labs typically have a different structure than tasks.
    This function filters to return only lab-type items.

    Args:
        items: List of all items from the backend.

    Returns:
        List of lab dictionaries.
    """
    labs = []
    for item in items:
        # Check if this is a lab (not a task)
        # Labs typically have 'type' field or specific naming pattern
        item_type = item.get("type", "")
        item_id = item.get("id", "")

        # Convert item_id to string for safe comparison
        item_id_str = str(item_id) if item_id is not None else ""

        # Labs are typically identified by having a type or being a parent item
        if item_type == "lab" or (item_id_str and item_id_str.startswith("lab-")):
            labs.append(item)

    # If no labs found with type filtering, try to find items that look like labs
    if not labs:
        for item in items:
            item_id = item.get("id", "")
            item_id_str = str(item_id) if item_id is not None else ""
            # Check if item has tasks (indicating it's a parent lab)
            if item.get("tasks") or "lab" in item_id_str.lower():
                labs.append(item)

    return labs


def _format_connect_error(error: httpx.ConnectError) -> str:
    """Format connection error into user-friendly message.

    Args:
        error: The connection error.

    Returns:
        Formatted error message with actual error details.
    """
    error_str = str(error).lower()

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
        if config.lms_api_base_url:
            return f"connection failed ({config.lms_api_base_url})"
        return "all connection attempts failed"
    else:
        return str(error)
