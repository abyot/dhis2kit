"""HTTP clients (sync & async) for DHIS2 with CRUD, paging, and analytics.

Highlights
----------
- Generic CRUD: get/post/put/patch/delete
- Metadata helpers: list_metadata, get_metadata, create/update/patch/delete_metadata
- Data helpers: push_data_value_set (import), pull_data_value_set (export)
- Analytics helper: get_analytics -> returns a Pydantic model
- Paging: list with page/pageSize/totalPages and iterators iter_metadata / aiter_metadata
- Logging + typed exceptions for clean error handling
"""

import logging
from typing import Any, AsyncGenerator, Dict, Generator, Iterable, Optional, Union
from urllib.parse import urlsplit, urlunsplit

import httpx

from .exceptions import AuthenticationError, NotFoundError, ServerError, ValidationError
from .models.analytics import AnalyticsResponse

logger = logging.getLogger("dhis2kit")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

Json = Dict[str, Any]


def _check_response(resp: httpx.Response) -> None:
    """
    Map HTTP errors to typed exceptions (without assuming JSON in the body).
    """
    status = resp.status_code
    if status in (401, 403):
        raise AuthenticationError(resp.text)
    if status == 404:
        raise NotFoundError(resp.text)
    # DHIS2 often uses 400/409 for bad params/payload/conflicts
    if status in (400, 409):
        raise ValidationError(resp.text)
    if 400 <= status < 500:
        raise ServerError(f"{status}: {resp.text}")
    if status >= 500:
        raise ServerError(f"{status}: {resp.text}")


def _extract_paging(payload: Dict[str, Any]) -> Dict[str, Optional[int]]:
    """
    Normalize DHIS2 paging info to a consistent dict.

    Supports either:
      - classic: {"pager": {"page": 1, "pageSize": 50, "pageCount": 4, "total": 200}}
      - flat:    {"page": 1, "pageSize": 50, "pageCount": 4, "total": 200}

    Returns: {"page": int|None, "pageSize": int|None, "pageCount": int|None, "total": int|None}
    """
    if "pager" in payload and isinstance(payload["pager"], dict):
        p = payload["pager"]
        return {
            "page": p.get("page"),
            "pageSize": p.get("pageSize"),
            "pageCount": p.get("pageCount"),
            "total": p.get("total"),
        }
    return {
        "page": payload.get("page"),
        "pageSize": payload.get("pageSize"),
        "pageCount": payload.get("pageCount"),
        "total": payload.get("total"),
    }


class Dhis2Client:
    """Synchronous DHIS2 client with CRUD, analytics, and paging helpers.

    Parameters
    ----------
    base_url : str
        DHIS2 API base, e.g. "https://play.dhis2.org/40.0.0/api"
    username : str
        Basic auth username.
    password : str
        Basic auth password.
    timeout : int, default 30
        Request timeout (seconds).
    """

    def __init__(self, base_url: str, username: str, password: str, timeout: int = 30):
        # Normalize base_url: strip, collapse '//' in path, drop trailing slash
        base = base_url.strip()
        scheme, netloc, path, query, frag = urlsplit(base)
        while "//" in path:
            path = path.replace("//", "/")
        self.base_url = urlunsplit((scheme, netloc, path.rstrip("/"), query, frag))
        self.auth = (username, password)
        self.client = httpx.Client(auth=self.auth, timeout=timeout)
        logger.debug("Initialized Dhis2Client for %s", self.base_url)

    def _url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _request(self, method: str, endpoint: str, **kwargs) -> Json:
        url = self._url(endpoint)
        logger.info("%s %s params=%s", method.upper(), url, kwargs.get("params"))

        resp = self.client.request(method, url, **kwargs)
        _check_response(resp)

        # No content? Return empty dict
        if resp.status_code == 204 or not resp.content:
            return {}

        # Expect JSON
        ctype = resp.headers.get("content-type", "").lower()
        if "application/json" not in ctype:
            raise ServerError(
                f"Expected JSON but got Content-Type='{ctype}' (status {resp.status_code}). "
                f"Body (truncated): {resp.text[:200]}"
            )
        try:
            return resp.json()
        except Exception as exc:
            raise ServerError(
                f"Failed to decode JSON response: {exc}. Body (truncated): {resp.text[:200]}"
            ) from exc

    # ---------- Generic CRUD ----------
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Json:
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, json: Optional[Json] = None) -> Json:
        return self._request("POST", endpoint, json=json)

    def put(self, endpoint: str, json: Optional[Json] = None) -> Json:
        return self._request("PUT", endpoint, json=json)

    def patch(self, endpoint: str, json: Optional[Json] = None) -> Json:
        return self._request("PATCH", endpoint, json=json)

    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Json:
        return self._request("DELETE", endpoint, params=params)

    # ---------- Metadata convenience (with paging) ----------
    def list_metadata(
        self,
        resource: str,
        *,
        fields: Union[str, Iterable[str]] = "id,displayName",
        page: Optional[int] = None,
        page_size: int = 50,
        total_pages: bool = False,
        collection_key: Optional[str] = None,
        **extra_params: Any,
    ) -> Json:
        """
        List metadata with optional paging.
        - resource: e.g., "dataElements", "organisationUnits"
        - fields: string or iterable, turned into comma-separated fields
        - page: request a specific page (1-based)
        - page_size: page size (default 50)
        - total_pages: ask server to include total page information ('totalPages=true')
        - collection_key: override collection key in response (defaults to resource)
        """
        params: Dict[str, Any] = {
            "fields": fields if isinstance(fields, str) else ",".join(fields),
            "pageSize": page_size,
        }
        if page is not None:
            params["page"] = page
        if total_pages:
            params["totalPages"] = "true"
        params.update(extra_params)
        coll_key = collection_key or resource
        out = self.get(f"{resource}.json", params=params)
        out.setdefault(coll_key, out.get(coll_key, []))
        return out

    def iter_metadata(
        self,
        resource: str,
        *,
        fields: Union[str, Iterable[str]] = "id,displayName",
        page_size: int = 100,
        start_page: int = 1,
        max_pages: Optional[int] = None,
        collection_key: Optional[str] = None,
        **extra_params: Any,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Iterate over all pages of a metadata resource, yielding items (dicts).
        Stops when pageCount is reached or when a page returns < page_size items.
        """
        coll_key = collection_key or resource
        page = start_page
        fetched_pages = 0
        while True:
            payload = self.list_metadata(
                resource,
                fields=fields,
                page=page,
                page_size=page_size,
                total_pages=True,
                collection_key=coll_key,
                **extra_params,
            )
            items = payload.get(coll_key, []) or []
            yield from items

            paging = _extract_paging(payload)
            page_count = paging.get("pageCount")
            if page_count is None:
                if len(items) < page_size:
                    break
                page += 1
            else:
                page += 1
                if page > page_count:
                    break
            fetched_pages += 1
            if max_pages is not None and fetched_pages >= max_pages:
                break

    def get_metadata(
        self,
        resource: str,
        uid: str,
        fields: Union[str, Iterable[str]] = "id,displayName",
        **extra_params,
    ) -> Json:
        params = {"fields": fields if isinstance(fields, str) else ",".join(fields)}
        params.update(extra_params)
        return self.get(f"{resource}/{uid}.json", params=params)

    def create_metadata(self, resource: str, payload: Json) -> Json:
        return self.post(f"{resource}", json=payload)

    def update_metadata(self, resource: str, uid: str, payload: Json) -> Json:
        return self.put(f"{resource}/{uid}", json=payload)

    def patch_metadata(self, resource: str, uid: str, payload: Json) -> Json:
        return self.patch(f"{resource}/{uid}", json=payload)

    def delete_metadata(self, resource: str, uid: str) -> Json:
        return self.delete(f"{resource}/{uid}")

    # ---------- Data helpers (dataValueSets) ----------
    def push_data_value_set(self, payload: Json) -> Json:
        return self.post("dataValueSets", json=payload)

    def pull_data_value_set(self, **params) -> Json:
        return self.get("dataValueSets", params=params)

    # ---------- Analytics ----------
    def get_analytics(self, **params) -> AnalyticsResponse:
        raw = self.get("analytics.json", params=params)
        return AnalyticsResponse(**raw)

    def close(self) -> None:
        logger.debug("Closing Dhis2Client")
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


class AsyncDhis2Client:
    """Asynchronous DHIS2 client with CRUD, analytics, and paging helpers."""

    def __init__(self, base_url: str, username: str, password: str, timeout: int = 30):
        base = base_url.strip()
        scheme, netloc, path, query, frag = urlsplit(base)
        while "//" in path:
            path = path.replace("//", "/")
        self.base_url = urlunsplit((scheme, netloc, path.rstrip("/"), query, frag))
        self.auth = (username, password)
        self.client = httpx.AsyncClient(auth=self.auth, timeout=timeout)
        logger.debug("Initialized AsyncDhis2Client for %s", self.base_url)

    def _url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    async def _request(self, method: str, endpoint: str, **kwargs) -> Json:
        url = self._url(endpoint)
        logger.info("%s %s params=%s", method.upper(), url, kwargs.get("params"))

        resp = await self.client.request(method, url, **kwargs)
        _check_response(resp)

        if resp.status_code == 204 or not resp.content:
            return {}

        ctype = resp.headers.get("content-type", "").lower()
        if "application/json" not in ctype:
            raise ServerError(
                f"Expected JSON but got Content-Type='{ctype}' (status {resp.status_code}). "
                f"Body (truncated): {resp.text[:200]}"
            )
        try:
            return resp.json()
        except Exception as exc:
            raise ServerError(
                f"Failed to decode JSON response: {exc}. Body (truncated): {resp.text[:200]}"
            ) from exc

    # ---------- Generic CRUD ----------
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Json:
        return await self._request("GET", endpoint, params=params)

    async def post(self, endpoint: str, json: Optional[Json] = None) -> Json:
        return await self._request("POST", endpoint, json=json)

    async def put(self, endpoint: str, json: Optional[Json] = None) -> Json:
        return await self._request("PUT", endpoint, json=json)

    async def patch(self, endpoint: str, json: Optional[Json] = None) -> Json:
        return await self._request("PATCH", endpoint, json=json)

    async def delete(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Json:
        return await self._request("DELETE", endpoint, params=params)

    # ---------- Metadata convenience (with paging) ----------
    async def list_metadata(
        self,
        resource: str,
        *,
        fields: Union[str, Iterable[str]] = "id,displayName",
        page: Optional[int] = None,
        page_size: int = 50,
        total_pages: bool = False,
        collection_key: Optional[str] = None,
        **extra_params: Any,
    ) -> Json:
        params: Dict[str, Any] = {
            "fields": fields if isinstance(fields, str) else ",".join(fields),
            "pageSize": page_size,
        }
        if page is not None:
            params["page"] = page
        if total_pages:
            params["totalPages"] = "true"
        params.update(extra_params)
        coll_key = collection_key or resource
        out = await self.get(f"{resource}.json", params=params)
        out.setdefault(coll_key, out.get(coll_key, []))
        return out

    async def aiter_metadata(
        self,
        resource: str,
        *,
        fields: Union[str, Iterable[str]] = "id,displayName",
        page_size: int = 100,
        start_page: int = 1,
        max_pages: Optional[int] = None,
        collection_key: Optional[str] = None,
        **extra_params: Any,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        coll_key = collection_key or resource
        page = start_page
        fetched_pages = 0
        while True:
            payload = await self.list_metadata(
                resource,
                fields=fields,
                page=page,
                page_size=page_size,
                total_pages=True,
                collection_key=coll_key,
                **extra_params,
            )
            items = payload.get(coll_key, []) or []
            for it in items:
                yield it
            paging = _extract_paging(payload)
            page_count = paging.get("pageCount")
            if page_count is None:
                if len(items) < page_size:
                    break
                page += 1
            else:
                page += 1
                if page > page_count:
                    break
            fetched_pages += 1
            if max_pages is not None and fetched_pages >= max_pages:
                break

    # ---------- Metadata CRUD (async) ----------
    async def create_metadata(
        self, resource: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """POST a new metadata object into a collection."""
        return await self.post(f"{resource}", json=payload)

    async def update_metadata(
        self, resource: str, uid: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """PUT (replace) an existing metadata object by UID."""
        return await self.put(f"{resource}/{uid}", json=payload)

    async def patch_metadata(
        self, resource: str, uid: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """PATCH (partial update) a metadata object by UID."""
        return await self.patch(f"{resource}/{uid}", json=payload)

    async def delete_metadata(self, resource: str, uid: str) -> Dict[str, Any]:
        """DELETE a metadata object by UID."""
        return await self.delete(f"{resource}/{uid}")

    # ---------- Data helpers ----------
    async def push_data_value_set(self, payload: Json) -> Json:
        return await self.post("dataValueSets", json=payload)

    async def pull_data_value_set(self, **params) -> Json:
        return await self.get("dataValueSets", params=params)

    # ---------- Analytics ----------
    async def get_analytics(self, **params) -> AnalyticsResponse:
        raw = await self.get("analytics.json", params=params)
        return AnalyticsResponse(**raw)

    async def aclose(self) -> None:
        logger.debug("Closing AsyncDhis2Client")
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.aclose()
