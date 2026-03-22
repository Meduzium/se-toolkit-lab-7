"""LMS API client for fetching academic data."""

from typing import Any

import httpx


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

    async def get_items(self) -> list[dict[str, Any]]:
        """Fetch all items (labs and tasks) from the backend.

        Returns:
            List of items (labs and tasks).

        Raises:
            httpx.HTTPError: If the request fails.
        """
        client = await self._get_client()
        response = await client.get("/items/")
        response.raise_for_status()
        return response.json()

    async def get_pass_rates(self, lab: str) -> list[dict[str, Any]]:
        """Fetch per-task pass rates for a specific lab.

        Args:
            lab: Lab identifier (e.g., "lab-01").

        Returns:
            List of pass rate dictionaries per task.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        client = await self._get_client()
        response = await client.get("/analytics/pass-rates", params={"lab": lab})
        response.raise_for_status()
        return response.json()

    async def get_learners(self) -> list[dict[str, Any]]:
        """Fetch enrolled learners.

        Returns:
            List of learner dictionaries.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        client = await self._get_client()
        response = await client.get("/learners/")
        response.raise_for_status()
        return response.json()

    async def get_scores(self, lab: str) -> dict[str, Any]:
        """Fetch score distribution for a lab.

        Args:
            lab: Lab identifier.

        Returns:
            Score distribution dictionary.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        client = await self._get_client()
        response = await client.get("/analytics/scores", params={"lab": lab})
        response.raise_for_status()
        return response.json()

    async def get_timeline(self, lab: str) -> list[dict[str, Any]]:
        """Fetch submissions timeline for a lab.

        Args:
            lab: Lab identifier.

        Returns:
            List of daily submission counts.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        client = await self._get_client()
        response = await client.get("/analytics/timeline", params={"lab": lab})
        response.raise_for_status()
        return response.json()

    async def get_groups(self, lab: str) -> list[dict[str, Any]]:
        """Fetch per-group performance for a lab.

        Args:
            lab: Lab identifier.

        Returns:
            List of group performance dictionaries.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        client = await self._get_client()
        response = await client.get("/analytics/groups", params={"lab": lab})
        response.raise_for_status()
        return response.json()

    async def get_top_learners(self, lab: str, limit: int = 5) -> list[dict[str, Any]]:
        """Fetch top learners for a lab.

        Args:
            lab: Lab identifier.
            limit: Maximum number of learners to return.

        Returns:
            List of top learner dictionaries.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        client = await self._get_client()
        response = await client.get(
            "/analytics/top-learners", params={"lab": lab, "limit": limit}
        )
        response.raise_for_status()
        return response.json()

    async def get_completion_rate(self, lab: str) -> dict[str, Any]:
        """Fetch completion percentage for a lab.

        Args:
            lab: Lab identifier.

        Returns:
            Completion rate dictionary.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        client = await self._get_client()
        response = await client.get("/analytics/completion-rate", params={"lab": lab})
        response.raise_for_status()
        return response.json()

    async def trigger_sync(self) -> dict[str, Any]:
        """Trigger ETL pipeline sync.

        Returns:
            Sync result dictionary.

        Raises:
            httpx.HTTPError: If the request fails.
        """
        client = await self._get_client()
        response = await client.post("/pipeline/sync", json={})
        response.raise_for_status()
        return response.json()
