"""LMS API client for fetching academic data."""

import httpx
from typing import Any


class LMSClient:
    """Client for LMS backend API."""

    def __init__(self, base_url: str, api_key: str) -> None:
        """Initialize LMS client.
        
        Args:
            base_url: Base URL of the LMS API.
            api_key: API key for authentication.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def get_labs(self) -> list[dict[str, Any]]:
        """Fetch available labs.
        
        Returns:
            List of lab dictionaries.
        """
        client = await self._get_client()
        response = await client.get("/api/labs")
        response.raise_for_status()
        return response.json()

    async def get_scores(self, user_id: str, lab_name: str) -> dict[str, Any]:
        """Fetch scores for a specific lab.
        
        Args:
            user_id: User identifier.
            lab_name: Name of the lab.
        
        Returns:
            Dictionary with scores information.
        """
        client = await self._get_client()
        response = await client.get(f"/api/scores/{user_id}/{lab_name}")
        response.raise_for_status()
        return response.json()

    async def health_check(self) -> dict[str, Any]:
        """Check LMS API health.
        
        Returns:
            Health status dictionary.
        """
        client = await self._get_client()
        response = await client.get("/api/health")
        response.raise_for_status()
        return response.json()
