import httpx


async def notify_prediction_ready(url: str, payload: dict, headers: dict | None = None) -> None:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, json=payload, headers=headers or {})
        response.raise_for_status()
