
# dhis2kit

A modern, typed **Python client for DHIS2** with:

- ✅ Pydantic **v2** models (DataElement, DataSet, OrganisationUnit, Analytics)
- ✅ **Sync & Async** clients (httpx)
- ✅ **DHIS2 paging**: `list_metadata`, `iter_metadata`, `aiter_metadata`
- ✅ CRUD for **metadata** and **data** (`dataValueSets`)
- ✅ Analytics helper (`/analytics.json` → Pydantic model)
- ✅ Structured logging & typed exceptions
- ✅ Full test suite with `httpx.MockTransport`
- ✅ Python **3.8+** support
- ✅ Command-line demo

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
  - [Sync client](#sync-client)
  - [Async client](#async-client)
- [Paging](#paging)
- [CRUD Operations](#crud-operations)
  - [Metadata](#metadata)
  - [Data (dataValueSets)](#data-datavalueSets)
- [Analytics API](#analytics-api)
- [Models (Pydantic v2)](#models-pydantic-v2)
- [Logging & Exceptions](#logging--exceptions)
- [Command-line Demo](#command-line-demo)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)
- [License](#license)

---

## Installation

Dev install (editable):

```bash
git clone <this-repo-or-extract-zip>
cd dhis2kit_release
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

> **Python:** 3.8+ (tested on 3.8–3.12 in CI).

---

## Quick Start

### Sync client

```python
from dhis2kit.client import Dhis2Client

with Dhis2Client("https://play.dhis2.org/40.0.0/api", "admin", "district") as client:
    # Single page list
    res = client.list_metadata(
        "dataElements",
        fields="id,displayName,valueType",
        page_size=5,
        total_pages=True
    )
    for de in res.get("dataElements", []):
        print(de["id"], de["displayName"], de.get("valueType"))
```

### Async client

```python
import asyncio
from dhis2kit.client import AsyncDhis2Client

async def main():
    async with AsyncDhis2Client("https://play.dhis2.org/40.0.0/api", "admin", "district") as client:
        page = await client.list_metadata("organisationUnits", fields="id,displayName,level", page_size=5)
        print([ou["displayName"] for ou in page.get("organisationUnits", [])])

asyncio.run(main())
```

---

## Paging

DHIS2 endpoints return paging in different shapes (legacy `pager` object or flat `page/pageCount`). `dhis2kit` supports both.

- **Single page**:
  ```python
  page2 = client.list_metadata("dataElements", page=2, page_size=100, total_pages=True)
  ```

- **Iterate all** (sync):
  ```python
  for item in client.iter_metadata("dataElements", fields="id,displayName", page_size=200):
      print(item["id"], item["displayName"])
  ```

- **Iterate all** (async, cap to first 5 pages):
  ```python
  async for ou in client.aiter_metadata("organisationUnits", fields="id,displayName", page_size=500, max_pages=5):
      print(ou["id"], ou["displayName"])
  ```

> If the server doesn’t expose `pageCount`, iteration stops when a page returns fewer than `page_size` items.

---

## CRUD Operations

### Metadata

```python
with Dhis2Client("https://play.dhis2.org/40.0.0/api", "admin", "district") as client:
    # List
    lst = client.list_metadata("dataElements", fields="id,displayName", page_size=10)

    # Get one
    uid = lst["dataElements"][0]["id"]
    de = client.get_metadata("dataElements", uid, fields="id,displayName,code")

    # Create (payload shape varies by DHIS2 version)
    # resp = client.create_metadata("optionSets", {"name": "My Option Set", "valueType": "TEXT"})

    # Update
    # resp = client.update_metadata("dataElements", uid, {"displayName": "Updated Name"})

    # Patch
    # resp = client.patch_metadata("dataElements", uid, {"shortName": "Upd"})

    # Delete
    # resp = client.delete_metadata("dataElements", uid)
```

**Async equivalents** (method names are the same, just `await` them):
- `await client.create_metadata(...)`
- `await client.update_metadata(...)`
- `await client.patch_metadata(...)`
- `await client.delete_metadata(...)`

### Data (`dataValueSets`)

```python
with Dhis2Client("https://play.dhis2.org/40.0.0/api", "admin", "district") as client:
    exported = client.pull_data_value_set(
        dataSet="lyLU2wR22tC", period="202201", orgUnit="ImspTQPwCqd", format="json"
    )
    print("Export keys:", list(exported.keys())[:5])

    # Example import payload (adapt per your DHIS2 import API)
    # payload = {
    #   "dataValues": [
    #       {"dataElement": "Uvn6LCg7dVU", "period": "202201", "orgUnit": "ImspTQPwCqd", "value": "12"}
    #   ]
    # }
    # resp = client.push_data_value_set(payload)
```

---

## Analytics API

```python
from dhis2kit.client import Dhis2Client

with Dhis2Client("https://play.dhis2.org/40.0.0/api", "admin", "district") as client:
    ar = client.get_analytics(
        dimension=["dx:Uvn6LCg7dVU", "pe:LAST_12_MONTHS"],
        filter="ou:ImspTQPwCqd",
        displayProperty="NAME",
    )
    print("Headers:", [h.get("name") for h in ar.headers])
    print("First rows:", ar.rows[:3])
```

Returns a Pydantic model:

```python
from dhis2kit.models.analytics import AnalyticsResponse

# ar is AnalyticsResponse
assert isinstance(ar, AnalyticsResponse)
```

---

## Models (Pydantic v2)

- `DataElement`, `CategoryCombo`, `CategoryOption`, `OptionSet`, `Option`
- `OrganisationUnit` (supports nesting: `parent` and `children`, plus `ancestors()`)
- `DataSet`
- `AnalyticsResponse`, `AnalyticsMetadata`

```python
from dhis2kit.models.dataelement import DataElement
from dhis2kit.models.organisation import OrganisationUnit

de = DataElement(id="de1", displayName="My Element")
ou = OrganisationUnit(id="ou1", displayName="Country", parent={"id":"ou0","displayName":"World"})
print([a.displayName for a in ou.ancestors()])  # -> ['World']
```

All models use:

```python
from pydantic import ConfigDict
model_config = ConfigDict(from_attributes=True)
```

---

## Logging & Exceptions

Enable verbose logs:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Typed exceptions you can catch:

- `AuthenticationError` (401/403)
- `NotFoundError` (404)
- `ServerError` (5xx or invalid JSON)
- `ValidationError` (client-side model validation use)

```python
from dhis2kit.exceptions import AuthenticationError, NotFoundError

try:
    client.get("dataElements.json")
except AuthenticationError:
    ...
except NotFoundError:
    ...
```

---

## Command-line Demo

We include a demo you can run:

```bash
python -m dhis2kit
```

It performs a small sync + async showcase against the DHIS2 demo server.

---

## Testing

Run the full suite:

```bash
pytest -q
```

What’s covered:
- Models (Pydantic)
- Sync client CRUD + error mapping
- Async client CRUD + iterator
- Paging (`iter_metadata`, `aiter_metadata`)
- All network calls are mocked using `httpx.MockTransport`

---

## Troubleshooting

- **`ModuleNotFoundError: No module named 'dhis2kit'`**
  Make sure you’re inside the virtualenv and have installed the package:
  ```bash
  pip install -e .
  ```

- **`pytest-asyncio` warnings about loop scope**
  We set defaults in `pytest.ini`. If you still see warnings, ensure your `pytest-asyncio` version matches `requirements.txt`.

- **Pandoc “pdflatex not found”** (if you convert docs to PDF)
  Install a LaTeX engine (e.g. `texlive-latex-base`) or use an alternative `--pdf-engine` like `wkhtmltopdf`.

- **DHIS2 import payload mismatches**
  Some DHIS2 versions expect import wrappers (e.g. `{"metadata": {...}}`) or import options. Adjust payloads per your server’s docs.

---

## CLI

Install (editable) and use the `dhis2kit` command:

```bash
pip install -e .
dhis2kit --help
```

You can pass server/credentials via flags or env:

export DHIS2_URL=http://localhost:8080/api
export DHIS2_USER=admin
export DHIS2_PASS=district

## Project Structure

```
dhis2kit_release/
├─ dhis2kit/
│  ├─ __init__.py
│  ├─ __main__.py      # CLI demo: python -m dhis2kit
│  ├─ client.py        # sync & async clients, CRUD, paging, analytics
│  ├─ exceptions.py    # typed exceptions
│  └─ models/
│     ├─ __init__.py
│     ├─ dataelement.py
│     ├─ dataset.py
│     ├─ organisation.py
│     └─ analytics.py
├─ examples/
│  ├─ example_crud_metadata.py
│  ├─ example_crud_data.py
│  └─ example_analytics.py
├─ tests/
│  ├─ conftest.py
│  ├─ test_models.py
│  ├─ test_client_sync.py
│  ├─ test_client_async.py
│  ├─ test_paging_sync.py
│  └─ test_paging_async.py
├─ pytest.ini
├─ requirements.txt
├─ setup.cfg
├─ pyproject.toml
└─ .github/workflows/ci.yml
```

---

