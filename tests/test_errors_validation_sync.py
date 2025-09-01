import httpx
import pytest

from dhis2kit.client import Dhis2Client
from dhis2kit.exceptions import ValidationError


def test_sync_400_maps_to_validation_error():
    # Mock a 400 Bad Request (typical DHIS2 validation error)
    transport = httpx.MockTransport(
        lambda req: httpx.Response(400, text="Bad request: invalid parameter")
    )
    client = Dhis2Client("http://localhost:8080/api", "user", "pass")
    client.client = httpx.Client(transport=transport)

    with pytest.raises(ValidationError) as exc:
        client.get(
            "dataElements.json", params={"fields": "id,name", "pageSize": "oops"}
        )
    assert "Bad request" in str(exc.value)

    client.close()


def test_sync_409_maps_to_validation_error():
    # Mock a 409 Conflict (e.g., duplicate UID, conflict on import)
    transport = httpx.MockTransport(
        lambda req: httpx.Response(409, text="Conflict: object already exists")
    )
    client = Dhis2Client("http://localhost:8080/api", "user", "pass")
    client.client = httpx.Client(transport=transport)

    with pytest.raises(ValidationError) as exc:
        client.post("dataElements", json={"id": "de1", "displayName": "Duplicate"})
    assert "Conflict" in str(exc.value)

    client.close()
