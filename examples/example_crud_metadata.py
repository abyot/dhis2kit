"""CRUD example for metadata."""

from dhis2kit.client import Dhis2Client


def main():
    with Dhis2Client(
        "https://play.dhis2.org/40.0.0/api", "admin", "district"
    ) as client:
        listed = client.list_metadata(
            "dataElements", fields="id,displayName", page_size=3, total_pages=True
        )
        print(
            "Listed dataElements:",
            [d["displayName"] for d in listed.get("dataElements", [])],
        )

        # Iterate with paging
        seen = []
        for it in client.iter_metadata(
            "dataElements", fields="id,displayName", page_size=3, max_pages=2
        ):
            seen.append(it["id"])
        print("Iterated ids (max 2 pages):", seen)


if __name__ == "__main__":
    main()
