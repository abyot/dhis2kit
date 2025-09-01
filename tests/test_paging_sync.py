import httpx

from dhis2kit.client import Dhis2Client


def test_iter_metadata_paging_sync():
    def handler(request: httpx.Request) -> httpx.Response:
        qs = dict(request.url.params)
        page = int(qs.get("page", "1"))
        page_size = int(qs.get("pageSize", "2"))
        total_pages = 2
        start = (page - 1) * page_size
        items = [
            {"id": f"de{start+i+1}", "displayName": f"DE {start+i+1}"}
            for i in range(page_size)
        ]
        payload = {
            "dataElements": items,
            "pager": {
                "page": page,
                "pageSize": page_size,
                "pageCount": total_pages,
                "total": page_size * total_pages,
            },
        }
        return httpx.Response(200, json=payload)

    client = Dhis2Client("https://example.org/api", "u", "p")
    client.client = httpx.Client(transport=httpx.MockTransport(handler))
    seen = [it["id"] for it in client.iter_metadata("dataElements", page_size=2)]
    assert seen == ["de1", "de2", "de3", "de4"]
    client.close()
