"""LLM API client for natural language processing."""

import httpx
from typing import Any


class LLMClient:
    """Client for LLM API (OpenRouter)."""

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

    async def chat(self, messages: list[dict[str, str]]) -> str:
        """Send a chat request to the LLM.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'.
        
        Returns:
            Response text from the LLM.
        """
        client = await self._get_client()
        response = await client.post(
            "/chat/completions",
            json={
                "model": self.model,
                "messages": messages,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    async def classify_intent(self, user_message: str) -> str:
        """Classify user intent from natural language message.
        
        Args:
            user_message: User's natural language message.
        
        Returns:
            Intent string (e.g., 'start', 'help', 'labs', 'scores', 'unknown').
        """
        system_prompt = (
            "You are an intent classifier for an LMS Telegram bot. "
            "Classify the user's message into one of these intents: "
            "start, help, labs, scores, health, unknown. "
            "Return only the intent name, nothing else."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        
        response = await self.chat(messages)
        return response.strip().lower()
