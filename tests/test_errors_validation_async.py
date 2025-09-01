import httpx
import pytest

from dhis2kit.client import AsyncDhis2Client
from dhis2kit.exceptions import ValidationError


@pytest.mark.asyncio
async def test_async_400_maps_to_validation_error():
    # Mock a 400 Bad Request
    transport = httpx.MockTransport(
        lambda req: httpx.Response(400, text="Bad request: invalid parameter")
    )
    client = AsyncDhis2Client("http://localhost:8080/api", "user", "pass")
    client.client = httpx.AsyncClient(transport=transport)

    with pytest.raises(ValidationError) as exc:
        await client.get(
            "dataElements.json", params={"fields": "id,name", "pageSize": "oops"}
        )
    assert "Bad request" in str(exc.value)

    await client.aclose()


@pytest.mark.asyncio
async def test_async_409_maps_to_validation_error():
    # Mock a 409 Conflict
    transport = httpx.MockTransport(
        lambda req: httpx.Response(409, text="Conflict: object already exists")
    )
    client = AsyncDhis2Client("http://localhost:8080/api", "user", "pass")
    client.client = httpx.AsyncClient(transport=transport)

    with pytest.raises(ValidationError) as exc:
        await client.post(
            "dataElements", json={"id": "de1", "displayName": "Duplicate"}
        )
    assert "Conflict" in str(exc.value)

    await client.aclose()
