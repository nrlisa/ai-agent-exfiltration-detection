from typing import Any


def to_detector_input(event: dict[str, Any]) -> dict[str, Any]:
    """Convert one CloudTrail event into monitor-visible evidence."""

    request = event.get("requestParameters") or {}
    identity = event.get("userIdentity") or {}
    additional = event.get("additionalEventData") or {}

    return {
        "event_time": event.get("eventTime"),
        "action": event.get("eventName"),
        "bucket": request.get("bucketName"),
        "object_key": request.get("key"),
        "identity": identity.get("arn"),
        "source_ip": event.get("sourceIPAddress"),
        "bytes_transferred_out": additional.get("bytesTransferredOut"),
        "error_code": event.get("errorCode"),
    }