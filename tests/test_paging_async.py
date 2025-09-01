import httpx
import pytest

from dhis2kit.client import AsyncDhis2Client


@pytest.mark.asyncio
async def test_aiter_metadata_paging_async():
    def handler(request: httpx.Request) -> httpx.Response:
        qs = dict(request.url.params)
        page = int(qs.get("page", "1"))
        page_size = int(qs.get("pageSize", "3"))
        total_pages = 3
        start = (page - 1) * page_size
        items = [
            {"id": f"ou{start+i+1}", "displayName": f"OU {start+i+1}"}
            for i in range(page_size)
        ]
        payload = {
            "organisationUnits": items,
            "page": page,
            "pageSize": page_size,
            "pageCount": total_pages,
            "total": page_size * total_pages,
        }
        return httpx.Response(200, json=payload)

    client = AsyncDhis2Client("https://example.org/api", "u", "p")
    client.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    ids = []
    async for it in client.aiter_metadata("organisationUnits", page_size=3):
        ids.append(it["id"])
    assert ids == ["ou1", "ou2", "ou3", "ou4", "ou5", "ou6", "ou7", "ou8", "ou9"]
    await client.aclose()
