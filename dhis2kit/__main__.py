"""Demo entrypoint: python -m dhis2kit"""

import asyncio
import logging

from .client import AsyncDhis2Client, Dhis2Client

logging.basicConfig(level=logging.INFO)


def demo_sync():
    print("=== DHIS2 Sync Client Demo ===")
    with Dhis2Client("http://localhost:8080/api", "admin", "district") as client:
        # Fetch first 5 data elements via single page
        data = client.list_metadata(
            "dataElements",
            fields="id,displayName,valueType",
            page_size=5,
            total_pages=True,
        )
        for de in data.get("dataElements", []):
            print(
                f"DataElement: {de.get('id')} | {de.get('displayName')} | {de.get('valueType')}"
            )

        # Iterate (paged) a few organisation units
        print("First 10 organisationUnits via iterator:")
        n = 0
        for ou in client.iter_metadata(
            "organisationUnits", fields="id,displayName,level", page_size=5, max_pages=2
        ):
            print(f"OU: {ou.get('id')} | {ou.get('displayName')} | L{ou.get('level')}")
            n += 1
            if n >= 10:
                break


async def demo_async():
    print("=== DHIS2 Async Client Demo ===")
    async with AsyncDhis2Client(
        "http://localhost:8080/api", "admin", "district"
    ) as client:
        # Iterate (paged) data elements
        count = 0
        async for de in client.aiter_metadata(
            "dataElements", fields="id,displayName", page_size=5, max_pages=2
        ):
            print(f"DE: {de.get('id')} | {de.get('displayName')}")
            count += 1
            if count >= 10:
                break


def main():
    demo_sync()
    asyncio.run(demo_async())


if __name__ == "__main__":
    main()
