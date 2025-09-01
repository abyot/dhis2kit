"""Data import/export example (dataValueSets)."""

from dhis2kit.client import Dhis2Client


def main():
    with Dhis2Client(
        "https://play.dhis2.org/40.0.0/api", "admin", "district"
    ) as client:
        exported = client.pull_data_value_set(
            dataSet="lyLU2wR22tC", period="202201", orgUnit="ImspTQPwCqd", format="json"
        )
        print("Export keys:", list(exported.keys())[:5])


if __name__ == "__main__":
    main()
