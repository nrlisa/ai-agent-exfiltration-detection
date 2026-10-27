
import copy
import gzip
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

SOURCE_DIR = Path("poc-data/cloudtrail-logs/experiment-2026-10-27")
OUTPUT_DIR = Path("poc-data/experiment-evidence/degraded")

TARGET_BUCKET = "fyp-experiment-data"
TARGET_KEY = "synthetic/experiment-test-data.txt"
IDENTITY_PLACEHOLDER = "MASKED"


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def floor_to_minute(timestamp):
    """Round an ISO 8601 timestamp down to the start of its minute."""
    value = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    value = value.replace(second=0, microsecond=0)
    return value.isoformat().replace("+00:00", "Z")


def main():
    if not SOURCE_DIR.exists():
        raise SystemExit(f"Source directory not found: {SOURCE_DIR}")

    files = sorted(SOURCE_DIR.rglob("*.json.gz"))
    if not files:
        raise SystemExit(f"No .json.gz files found in {SOURCE_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    original_hashes = {path: sha256_file(path) for path in files}
    degraded_events = []
    errors = []

    for path in files:
        try:
            with gzip.open(path, "rt", encoding="utf-8") as file:
                document = json.load(file)
        except (OSError, EOFError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: {exc}")
            continue

        for index, event in enumerate(document.get("Records", [])):
            request = event.get("requestParameters") or {}

            if (
                event.get("eventSource") != "s3.amazonaws.com"
                or event.get("eventName") != "GetObject"
                or request.get("bucketName") != TARGET_BUCKET
                or request.get("key") != TARGET_KEY
            ):
                continue

            degraded = copy.deepcopy(event)

            # 1. Remove the bucket name.
            degraded_request = degraded.get("requestParameters") or {}
            degraded_request.pop("bucketName", None)
            if degraded_request:
                degraded["requestParameters"] = degraded_request
            else:
                degraded.pop("requestParameters", None)

            # 2. Reduce timestamp precision to the minute.
            if degraded.get("eventTime"):
                degraded["eventTime"] = floor_to_minute(
                    degraded["eventTime"]
                )

            # 3. Mask the specific identity.
            identity = degraded.setdefault("userIdentity", {})
            identity["arn"] = IDENTITY_PLACEHOLDER

            # Keep source provenance outside the event given to monitors.
            degraded_events.append({
                "source_file": str(path),
                "source_record_index": index,
                "event": degraded,
            })

    # Save transformed events separately from original evidence.
    output_file = OUTPUT_DIR / "degraded-events.json"
    with output_file.open("w", encoding="utf-8") as file:
        json.dump(degraded_events, file, indent=2)
        file.write("\n")

    # Verify all three transformations.
    validation_errors = []
    for item in degraded_events:
        event = item["event"]
        request = event.get("requestParameters") or {}
        identity = event.get("userIdentity") or {}

        if "bucketName" in request:
            validation_errors.append("Bucket name was not removed.")

        if event.get("eventTime", "").endswith("Z"):
            try:
                parsed = datetime.fromisoformat(
                    event["eventTime"].replace("Z", "+00:00")
                )
                if parsed.second != 0 or parsed.microsecond != 0:
                    validation_errors.append("Timestamp is not minute-level.")
            except ValueError:
                validation_errors.append("Invalid degraded timestamp.")

        if identity.get("arn") != IDENTITY_PLACEHOLDER:
            validation_errors.append("Identity was not masked.")

    # Verify source files were not modified.
    unchanged = all(
        sha256_file(path) == original_hash
        for path, original_hash in original_hashes.items()
    )

    print(f"Source files checked: {len(files)}")
    print(f"Matching events degraded: {len(degraded_events)}")
    print(f"Output: {output_file}")
    print(f"Original source files unchanged: {unchanged}")
    print(f"Transformation validation errors: {len(validation_errors)}")
    print(f"Unreadable source files: {len(errors)}")

    for message in validation_errors + errors:
        print(f"WARNING: {message}")

    if validation_errors or not unchanged:
        raise SystemExit("Validation failed; inspect warnings before proceeding.")

    if errors:
        raise SystemExit("Some source files could not be read; review warnings.")

    if not degraded_events:
        raise SystemExit("No matching events were found to degrade.")

    print("Degraded-evidence validation passed.")


if __name__ == "__main__":
    main()
