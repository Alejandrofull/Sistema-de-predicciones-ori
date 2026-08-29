import httpx


class ExternalAPIClient:
    async def get_json(self, url: str, headers: dict | None = None, params: dict | None = None):
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(url, headers=headers or {}, params=params or {})
            response.raise_for_status()
            return response.json()
