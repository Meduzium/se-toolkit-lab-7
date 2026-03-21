"""Base handler interface and types."""

from typing import Protocol


class HandlerResult(Protocol):
    """Result of a handler execution."""

    text: str
    success: bool


def create_result(text: str, success: bool = True) -> dict:
    """Create a handler result dictionary.
    
    Args:
        text: Response text to return to the user.
        success: Whether the handler executed successfully.
    
    Returns:
        Dictionary with 'text' and 'success' keys.
    """
    return {"text": text, "success": success}
