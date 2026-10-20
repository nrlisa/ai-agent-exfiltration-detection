import gzip
import json
from pathlib import Path

LOG_DIR = Path("poc-data/cloudtrail-logs")
TARGET_BUCKET = "fyp-persistence-test"
TARGET_KEY = "synthetic/test-data.txt"


def load_events():
    """Read CloudTrail-format records from compressed JSON files."""
    for path in LOG_DIR.rglob("*.json.gz"):
        with gzip.open(path, "rt", encoding="utf-8") as file:
            document = json.load(file)

        for event in document.get("Records", []):
            yield event


def main():
    matches = {}

    for event in load_events():
        request = event.get("requestParameters") or {}

        if (
            event.get("eventSource") != "s3.amazonaws.com"
            or event.get("eventName") != "GetObject"
            or request.get("bucketName") != TARGET_BUCKET
            or request.get("key") != TARGET_KEY
        ):
            continue

        # Avoid duplicate records from overlapping downloaded folders.
        identity = event.get("eventID") or (
            event.get("eventTime"),
            event.get("eventName"),
            request.get("bucketName"),
            request.get("key"),
            event.get("sourceIPAddress"),
        )
        matches[identity] = event

    print(f"Matching GetObject events: {len(matches)}")

    for event in sorted(
        matches.values(),
        key=lambda item: item.get("eventTime", ""),
    ):
        request = event.get("requestParameters") or {}
        user = event.get("userIdentity") or {}

        print(f"\nTime:       {event.get('eventTime')}")
        print(f"Action:     {event.get('eventName')}")
        print(f"Bucket:     {request.get('bucketName')}")
        print(f"Object:     {request.get('key')}")
        print(f"Identity:   {user.get('arn', 'Unknown')}")
        print(f"Source IP:  {event.get('sourceIPAddress')}")
        print(f"Error:      {event.get('errorCode')}")


if __name__ == "__main__":
    main()