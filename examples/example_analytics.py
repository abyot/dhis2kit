"""Analytics usage example."""

from dhis2kit.client import Dhis2Client


def main():
    with Dhis2Client(
        "https://play.dhis2.org/40.0.0/api", "admin", "district"
    ) as client:
        ar = client.get_analytics(
            dimension=["dx:Uvn6LCg7dVU", "pe:LAST_12_MONTHS"],
            filter="ou:ImspTQPwCqd",
            displayProperty="NAME",
        )
        print("Headers:", [h.get("name") for h in ar.headers])
        print("First rows:", ar.rows[:3])


if __name__ == "__main__":
    main()
