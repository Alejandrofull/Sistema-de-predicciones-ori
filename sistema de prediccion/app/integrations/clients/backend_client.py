import httpx


class BackendClient:
    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    async def post(self, path: str, payload: dict) -> dict:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(f"{self.base_url}/{path.lstrip('/')}", json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
