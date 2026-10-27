from datetime import datetime
from typing import Any, Dict, List

import httpx


class ElexonClient:
    def __init__(self, base_url: str = "https://data.elexon.co.uk/bmrs/api/v1"):
        self.base_url = base_url.rstrip("/")

    async def fetch_dataset(self, dataset: str, params: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/datasets/{dataset}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict):
                # Common shapes: {"data": [...]}
                if "data" in data and isinstance(data["data"], list):
                    return data["data"]
                # Some responses may differ; return empty list if unexpected
                return []
            if isinstance(data, list):
                return data
            return []
