import httpx
import pandas as pd


class APIExporter:
    async def export(self, data: pd.DataFrame, url: str, headers: dict | None = None) -> dict:
        payload = data.to_dict(orient="records")
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, json=payload, headers=headers or {})
            response.raise_for_status()
            try:
                return response.json()
            except ValueError:
                return {"status_code": response.status_code, "text": response.text}
