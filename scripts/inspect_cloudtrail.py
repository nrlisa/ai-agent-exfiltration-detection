
import argparse
import gzip
import json
import sys
from pathlib import Path

LOG_DIR = Path("poc-data/cloudtrail-logs")

TARGETS = {
    "experiment": {
        "bucket": "fyp-experiment-data",
        "key": "synthetic/experiment-test-data.txt",
    },
    "old-poc": {
        "bucket": "fyp-persistence-test",
        "key": "synthetic/test-data.txt",
    },
}


def load_events(log_dir):
    """Read CloudTrail-format records from local compressed JSON files."""
    if not log_dir.exists():
        print(
            f"Error: log directory does not exist: {log_dir}",
            file=sys.stderr,
        )
        print(
            "Download the relevant CloudTrail .json.gz files into this "
            "directory before inspecting them.",
            file=sys.stderr,
        )
        return

    files = sorted(log_dir.rglob("*.json.gz"))

    if not files:
        print(f"No .json.gz files found in: {log_dir}", file=sys.stderr)
        return

    for path in files:
        try:
            with gzip.open(path, "rt", encoding="utf-8") as file:
                document = json.load(file)

            if not isinstance(document, dict):
                print(
                    f"Warning: unexpected JSON structure in {path}",
                    file=sys.stderr,
                )
                continue

            records = document.get("Records", [])
            if not isinstance(records, list):
                print(
                    f"Warning: 'Records' is not a list in {path}",
                    file=sys.stderr,
                )
                continue

            for event in records:
                if isinstance(event, dict):
                    yield path, event

        except (OSError, EOFError, gzip.BadGzipFile, json.JSONDecodeError,
                UnicodeDecodeError) as exc:
            print(
                f"Warning: skipping unreadable log {path}: {exc}",
                file=sys.stderr,
            )


def get_event_identity(event):
    """Return a stable deduplication key where possible."""
    event_id = event.get("eventID")
    if event_id:
        return event_id

    request = event.get("requestParameters") or {}
    user = event.get("userIdentity") or {}

    return (
        event.get("eventTime"),
        event.get("eventName"),
        request.get("bucketName"),
        request.get("key"),
        user.get("arn"),
        event.get("sourceIPAddress"),
    )


def main():
    parser = argparse.ArgumentParser(
        description="Inspect locally downloaded CloudTrail-format S3 events."
    )
    parser.add_argument(
        "--target",
        choices=TARGETS.keys(),
        default="experiment",
        help=(
            "Object to inspect: 'experiment' (default) or 'old-poc'."
        ),
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=LOG_DIR,
        help=f"Directory containing .json.gz files (default: {LOG_DIR}).",
    )
    args = parser.parse_args()

    target = TARGETS[args.target]
    target_bucket = target["bucket"]
    target_key = target["key"]

    matches = {}
    files_seen = set()

    for path, event in load_events(args.log_dir):
        files_seen.add(path)
        request = event.get("requestParameters") or {}

        if (
            event.get("eventSource") != "s3.amazonaws.com"
            or event.get("eventName") != "GetObject"
            or request.get("bucketName") != target_bucket
            or request.get("key") != target_key
        ):
            continue

        matches.setdefault(get_event_identity(event), (path, event))

    print(f"Target:      {args.target}")
    print(f"Bucket:      {target_bucket}")
    print(f"Object:      {target_key}")
    print(f"Log folder:  {args.log_dir}")
    print(f"Files read:  {len(files_seen)}")
    print(f"Matching GetObject events: {len(matches)}")

    for path, event in sorted(
        matches.values(),
        key=lambda item: item[1].get("eventTime") or "",
    ):
        request = event.get("requestParameters") or {}
        user = event.get("userIdentity") or {}
        additional = event.get("additionalEventData") or {}

        print("\n" + "-" * 60)
        print(f"Time:               {event.get('eventTime', 'Unknown')}")
        print(f"Action:             {event.get('eventName', 'Unknown')}")
        print(f"Bucket:             {request.get('bucketName', 'Unknown')}")
        print(f"Object:             {request.get('key', 'Unknown')}")
        print(f"Identity:           {user.get('arn', 'Unknown')}")
        print(f"Access key ID:      {user.get('accessKeyId') or 'Not recorded'}")
        print(f"Source IP:          {event.get('sourceIPAddress', 'Unknown')}")
        print(f"Bytes transferred:  {additional.get('bytesTransferredOut', 'Not recorded')}")
        print(f"Error:              {event.get('errorCode') or 'None recorded'}")
        print(f"User agent:         {event.get('userAgent', 'Unknown')}")
        print(f"Event ID:           {event.get('eventID', 'Not recorded')}")
        print(f"Evidence file:      {path}")


if __name__ == "__main__":
    main()
