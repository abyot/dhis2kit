import pytest
import pytest_asyncio

from dhis2kit.client import AsyncDhis2Client, Dhis2Client


@pytest.fixture
def sync_client():
    c = Dhis2Client("https://example.org/api", "user", "pass")
    yield c
    c.close()


@pytest_asyncio.fixture
async def async_client():
    c = AsyncDhis2Client("https://example.org/api", "user", "pass")
    yield c
    await c.aclose()


@pytest.fixture
def sample_dataelements():
    return {
        "dataElements": [{"id": "de1", "displayName": "DE1", "valueType": "NUMBER"}]
    }


@pytest.fixture
def sample_orgunits():
    return {"organisationUnits": [{"id": "ou1", "displayName": "Country", "level": 1}]}


@pytest.fixture
def sample_analytics():
    return {
        "headers": [{"name": "dx", "column": "dx", "valueType": "TEXT"}],
        "rows": [["Uvn6LCg7dVU"]],
        "metaData": {"items": {"Uvn6LCg7dVU": {"name": "ANC 1 Coverage"}}},
    }
