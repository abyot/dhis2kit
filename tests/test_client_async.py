import httpx
import pytest

from dhis2kit.models.organisation import OrganisationUnit


@pytest.mark.asyncio
async def test_async_list_orgunits(async_client, sample_orgunits):
    async_client.client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda req: httpx.Response(200, json=sample_orgunits)
        )
    )
    data = await async_client.list_metadata(
        "organisationUnits", fields="id,displayName"
    )
    ous = [OrganisationUnit(**ou) for ou in data.get("organisationUnits", [])]
    assert ous[0].id == "ou1"
    await async_client.client.aclose()


@pytest.mark.asyncio
async def test_async_delete(async_client):
    async_client.client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda req: httpx.Response(200, json={"deleted": True})
        )
    )
    resp = await async_client.delete_metadata("dataElements", "abc")
    assert resp["deleted"] is True
    await async_client.client.aclose()
