"""Handler for /scores command."""

import asyncio

import httpx

from config import config
from services.lms_client import LMSClient
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
            "⚠️ Please specify a lab name.\n\n"
            "Usage example:\n"
            "/scores lab-04\n\n"
            "Available labs: use /labs to see the list."
        )
        return create_result(text)

    return asyncio.run(_fetch_scores_async(lab_name))


async def _fetch_scores_async(lab_name: str) -> dict:
    """Async scores fetch implementation.

    Args:
        lab_name: Name of the lab.

    Returns:
        Handler result with scores information.
    """
    client = LMSClient(config.lms_api_base_url, config.lms_api_key)

    try:
        # First, get pass rates
        pass_rates = await client.get_pass_rates(lab_name)

        # Also get items to find tasks for this lab
        items = await client.get_items()
        lab_tasks = _get_tasks_for_lab(items, lab_name)

        # If we have pass rates, display them
        if pass_rates:
            lines = [f"📈 Pass rates for {lab_name}:"]

            for rate in pass_rates:
                task_name = rate.get("task_name", rate.get("task", rate.get("name", "Unknown")))
                pass_rate = rate.get("pass_rate", rate.get("rate", 0))
                attempts = rate.get("attempts", rate.get("count", 0))

                # Format percentage
                percentage = f"{pass_rate:.1f}%" if isinstance(pass_rate, (int, float)) else str(pass_rate)

                if attempts > 0:
                    lines.append(f"- {task_name}: {percentage} ({attempts} attempts)")
                else:
                    lines.append(f"- {task_name}: {percentage}")

            text = "\n".join(lines)
            return create_result(text)

        # No pass rates - show task list instead
        if lab_tasks:
            lines = [f"📋 Tasks for {lab_name}:"]
            for task in lab_tasks:
                task_title = task.get("title", "Unknown task")
                lines.append(f"- {task_title}")
            lines.append("")
            lines.append("📊 Pass rate data will appear here once students submit their work.")
            text = "\n".join(lines)
            return create_result(text)

        # Lab not found
        text = f"❌ Lab '{lab_name}' not found. Use /labs to see available labs."
        return create_result(text, success=False)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            text = f"❌ Lab '{lab_name}' not found. Use /labs to see available labs."
        else:
            error_msg = f"HTTP {e.response.status_code} {e.response.reason_phrase}"
            text = f"❌ Backend error: {error_msg}. The backend service may be down."
        return create_result(text, success=False)

    except httpx.ConnectError as e:
        error_msg = _format_connect_error(e)
        text = f"❌ Backend error: {error_msg}. Check that the services are running."
        return create_result(text, success=False)

    except httpx.HTTPError as e:
        error_msg = str(e) or "unknown error"
        text = f"❌ Backend error: {error_msg}."
        return create_result(text, success=False)

    finally:
        await client.close()


def _get_tasks_for_lab(items: list[dict], lab_name: str) -> list[dict]:
    """Get tasks for a specific lab from items list.

    Args:
        items: List of all items (labs and tasks).
        lab_name: Lab identifier (e.g., "lab-04" or "4").

    Returns:
        List of task dictionaries for the lab.
    """
    # Try to find the lab by matching title
    lab_id = None

    # Normalize lab_name: "lab-04" -> "lab 04", "lab-4", "4"
    lab_name_normalized = lab_name.lower().replace("-", " ").replace("_", " ")

    for item in items:
        if item.get("type") == "lab":
            title = item.get("title", "").lower()
            item_id = str(item.get("id", ""))

            # Check if lab name matches title or ID
            if (lab_name_normalized in title or
                lab_name.lower() in title or
                item_id == lab_name or
                item_id == lab_name.lstrip("lab-").lstrip("0")):
                lab_id = item.get("id")
                break

    if not lab_id:
        return []

    # Find all tasks with this parent_id
    tasks = []
    for item in items:
        if item.get("type") == "task" and item.get("parent_id") == lab_id:
            tasks.append(item)

    return tasks


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
