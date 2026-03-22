"""LLM API client for natural language processing with tool calling support."""

import httpx
import json
from typing import Any


class LLMClient:
    """Client for LLM API (OpenRouter) with tool calling support."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        model: str = "openrouter/free",
    ) -> None:
        """Initialize LLM client.

        Args:
            api_key: API key for authentication.
            base_url: Base URL of the LLM API.
            model: Model name to use.
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Send a chat request to the LLM with optional tool calling.

        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            tools: Optional list of tool definitions for function calling.

        Returns:
            Response dictionary with 'content' and optionally 'tool_calls'.
        """
        client = await self._get_client()
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        response = await client.post("/chat/completions", json=payload)
        response.raise_for_status()
        data = response.json()

        choice = data["choices"][0]
        message = choice["message"]

        result = {
            "content": message.get("content", ""),
            "tool_calls": [],
        }

        if "tool_calls" in message and message["tool_calls"]:
            for tc in message["tool_calls"]:
                result["tool_calls"].append({
                    "id": tc["id"],
                    "name": tc["function"]["name"],
                    "arguments": tc["function"]["arguments"],
                })

        return result

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Get all 9 tool definitions for LLM tool calling.

        Returns:
            List of tool schemas for the LLM.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_items",
                    "description": "Get list of all labs and tasks. Use this to discover available labs.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_learners",
                    "description": "Get list of enrolled students and their groups. Use for questions about enrollment or student lists.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_scores",
                    "description": "Get score distribution (4 buckets: 0-25, 26-50, 51-75, 76-100) for a specific lab.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                            },
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_pass_rates",
                    "description": "Get per-task average scores and attempt counts for a lab. Use for detailed performance analysis.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                            },
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_timeline",
                    "description": "Get submissions per day for a lab. Use for activity timeline questions.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                            },
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_groups",
                    "description": "Get per-group average scores and student counts for a lab. Use to compare group performance.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                            },
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_top_learners",
                    "description": "Get top N learners by average score for a lab. Use for leaderboard questions.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Number of top learners to return (default: 5)",
                            },
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_completion_rate",
                    "description": "Get completion rate percentage for a lab (percentage of learners who scored >= 60).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lab": {
                                "type": "string",
                                "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                            },
                        },
                        "required": ["lab"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "trigger_sync",
                    "description": "Trigger ETL pipeline sync to refresh data from autochecker. Use when user asks to update or refresh data.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
        ]
