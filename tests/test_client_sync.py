import httpx
import pytest

from dhis2kit.exceptions import AuthenticationError, NotFoundError, ServerError


def test_sync_list_metadata(sync_client, sample_dataelements):
    transport = httpx.MockTransport(
        lambda req: httpx.Response(200, json=sample_dataelements)
    )
    sync_client.client = httpx.Client(transport=transport)
    data = sync_client.list_metadata("dataElements", fields="id,displayName")
    assert data["dataElements"][0]["id"] == "de1"


def test_sync_get_metadata_404(sync_client):
    transport = httpx.MockTransport(lambda req: httpx.Response(404))
    sync_client.client = httpx.Client(transport=transport)
    with pytest.raises(NotFoundError):
        sync_client.get_metadata("dataElements", "does-not-exist")


def test_sync_errors(sync_client):
    auth_t = httpx.MockTransport(lambda req: httpx.Response(401))
    sync_client.client = httpx.Client(transport=auth_t)
    with pytest.raises(AuthenticationError):
        sync_client.get("dataElements.json")

    server_t = httpx.MockTransport(lambda req: httpx.Response(500))
    sync_client.client = httpx.Client(transport=server_t)
    with pytest.raises(ServerError):
        sync_client.get("dataElements.json")


def test_sync_crud_calls(sync_client):
    sync_client.client = httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"status": "OK", "httpStatus": 200})
        )
    )
    resp = sync_client.create_metadata("dataElements", {"name": "X"})
    assert resp.get("status") == "OK"

    sync_client.client = httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"httpStatus": 200})
        )
    )
    resp = sync_client.update_metadata("dataElements", "abc", {"name": "Y"})
    assert resp["httpStatus"] == 200

    sync_client.client = httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"patched": True})
        )
    )
    resp = sync_client.patch_metadata("dataElements", "abc", {"shortName": "Y"})
    assert resp["patched"] is True

    sync_client.client = httpx.Client(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"deleted": True})
        )
    )
    resp = sync_client.delete_metadata("dataElements", "abc")
    assert resp["deleted"] is True
