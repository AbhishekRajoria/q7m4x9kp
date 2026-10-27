from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import httpx


class ElexonClient:
    def __init__(self, base_url: str = "https://data.elexon.co.uk/bmrs/api/v1"):
        self.base_url = base_url.rstrip("/")

    async def fetch_dataset(self, dataset: str, params: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/datasets/{dataset}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, dict):
                    if "data" in data and isinstance(data["data"], list):
                        return data["data"]
                    return []
                if isinstance(data, list):
                    return data
                return []
        except (httpx.TimeoutException, httpx.HTTPStatusError, ValueError) as e:
            raise RuntimeError(f"Failed to fetch {dataset}: {e}") from e

    async def fetch_dataset_chunked(
        self,
        dataset: str,
        publish_from: datetime,
        publish_to: datetime,
        chunk_hours: int = 12,
    ) -> List[Dict[str, Any]]:
        """Fetch in chunks by publishDateTime range to avoid truncation."""
        results: List[Dict[str, Any]] = []
        chunk_delta = timedelta(hours=chunk_hours)
        current = publish_from
        while current < publish_to:
            chunk_end = min(current + chunk_delta, publish_to)
            params = {
                "format": "json",
                "publishDateTimeFrom": current.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "publishDateTimeTo": chunk_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            chunk = await self.fetch_dataset(dataset, params)
            results.extend(chunk)
            current = chunk_end
        return results
