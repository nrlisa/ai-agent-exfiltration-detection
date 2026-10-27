
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import boto3
from botocore.config import Config
from dotenv import load_dotenv

# Load local experiment credentials from .env
load_dotenv()

S3_ENDPOINT = "http://localhost:4567"
BUCKET = "fyp-experiment-data"
OBJECT_KEY = "synthetic/experiment-test-data.txt"
RECEIVER_URL = "http://127.0.0.1:8080/transfer"

OUTPUT_DIR = Path("poc-data/agent-logs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Require dedicated experiment credentials; do not fall back to test/test.
ACCESS_KEY = os.getenv("EXPERIMENT_AGENT_ACCESS_KEY")
SECRET_KEY = os.getenv("EXPERIMENT_AGENT_SECRET_KEY")

if not ACCESS_KEY or not SECRET_KEY:
    raise RuntimeError(
        "Missing EXPERIMENT_AGENT_ACCESS_KEY or "
        "EXPERIMENT_AGENT_SECRET_KEY in .env"
    )

# Local Floci S3 client using the experiment-agent IAM identity.
s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name="us-east-1",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    config=Config(s3={"addressing_style": "path"}),
)

started_at = datetime.now(timezone.utc).isoformat()

# Retrieve the synthetic source object.
response = s3.get_object(Bucket=BUCKET, Key=OBJECT_KEY)
with response["Body"] as body:
    payload = body.read()

payload_hash = hashlib.sha256(payload).hexdigest()

# Send the retrieved data to the local receiver.
request = Request(
    RECEIVER_URL,
    data=payload,
    headers={"Content-Type": "application/octet-stream"},
    method="POST",
)

with urlopen(request, timeout=5) as result:
    receiver_response = json.loads(result.read().decode("utf-8"))
    status_code = result.status

record = {
    "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"),
    "started_at": started_at,
    "s3_bucket": BUCKET,
    "s3_key": OBJECT_KEY,
    "bytes_read": len(payload),
    "payload_sha256": payload_hash,
    "receiver_url": RECEIVER_URL,
    "receiver_status": status_code,
    "receiver_response": receiver_response,
}

log_path = OUTPUT_DIR / "agent-runs.jsonl"
with log_path.open("a", encoding="utf-8") as f:
    f.write(json.dumps(record) + "\n")

print(json.dumps(record, indent=2))
