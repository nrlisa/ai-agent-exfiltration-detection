# Floci Proof of Concept (PoC) Documentation

**Project:** AI-Agent Data Exfiltration Detection Framework  
**FYP Title:** Design and Evaluation of Monitoring Strategies for Detecting AI-Agent Data Exfiltration under Incomplete Cloud Audit Evidence  
**Status:** Core local S3-to-receiver pipeline & persistence verified  
**Date:** 20 October 2026 | **Environment:** Windows, Git Bash, Docker, AWS CLI, Python/boto3

---

## 1. Purpose & Scope

Validates the local cloud-emulation testbed (Floci) for the FYP baseline:
- S3-compatible synthetic data storage and retrieval (AWS CLI & Python/boto3 agent).
- CloudTrail-format audit event generation and delivery for object-level access.
- Exfiltration to a local HTTP receiver with SHA-256 integrity verification.
- State and audit log persistence across container restarts.

> **Note:** Uses synthetic data in a local emulator; does not evaluate monitoring strategies or the full 520-run experimental matrix.

---

## 2. Architecture & Pipeline

```text
Synthetic S3 Object
       │
       ▼
Floci S3 API (localhost:4567) ──► S3 Audit Logs (fyp-poc-trail)
       │
       ▼
Python Agent (boto3)
       │ HTTP POST /transfer
       ▼
Local Receiver (127.0.0.1:8080) ──► Transfers JSONL + SHA-256 Hash
```

### 2.1 Floci Container & Volume Setup
Persistent container `floci-persistent` mapped to port `4567` (`FLOCI_STORAGE_MODE=persistent`, `/app/data` mounted on named volume `floci-persistent-data`).

> **Evidence (SS-01 - Container & Volume Setup):**  
> ![SS-01: Floci Container & Volume](evidences/01-floci-container-volume.png)

### 2.2 Components Summary

| Component | Identifier / Path | Purpose |
| :--- | :--- | :--- |
| **Emulator** | Container `floci-persistent` (port `4567`) | Local S3/CloudTrail emulator (vol: `floci-persistent-data`) |
| **S3 Storage** | Bucket `fyp-persistence-test` | Stores synthetic object & CloudTrail audit logs |
| **Test Object** | `synthetic/test-data.txt` | 75-byte synthetic payload |
| **Audit Trail** | `fyp-poc-trail` (region `us-east-1`) | Captures management & S3 data events (`GetObject`) |
| **Agent** | `src/agent/agent.py` | Retrieves object via boto3 and forwards to receiver |
| **Receiver** | `src/receiver/server.py` | Accepts POST payload (≤1 MiB) & logs transfer metadata |
| **Telemetry** | `poc-data/agent-logs/agent-runs.jsonl`<br>`poc-data/receiver-logs/transfers.jsonl` | Agent run logs and receiver-side integrity records |
| **Audit Logs** | `poc-data/cloudtrail-logs/AWSLogs/` | Synced compressed JSON log evidence |
| **Inspector** | `scripts/inspect_cloudtrail.py` | Deduplicates and parses CloudTrail S3 events |

---

## 3. Synthetic Test Payload

- **S3 Key:** `synthetic/test-data.txt`
- **Size:** 75 bytes
- **SHA-256:** `1819059edc21d93eebbe0c452a51a6d6d43923833c3140a5f9939f36b5aa5276`
- **Content:**
  ```text
  SYNTHETIC TEST DATA ONLY
  Record A: demo-value-001
  Record B: demo-value-002
  ```

---

## 4. Configuration & Verification Commands

### 4.1 Verify STS Identity
```bash
aws --endpoint-url=http://localhost:4567 sts get-caller-identity
```
> **Evidence (SS-02 - Floci API Identity):**  
> ![SS-02: Floci API Identity](evidences/02-floci-api-identity.png)

### 4.2 Verify S3 Object Retrieval
```bash
aws --endpoint-url=http://localhost:4567 s3api get-object \
  --bucket fyp-persistence-test \
  --key synthetic/test-data.txt /tmp/floci-persistence-test.txt
```
> **Evidence (SS-03 - Synthetic S3 Object Retrieval):**  
> ![SS-03: Synthetic S3 Object](evidences/03-synthetic-s3-object.png)

### 4.3 Configure & Verify CloudTrail
```bash
# Set event selectors for S3 object-level data events
aws --endpoint-url=http://localhost:4567 cloudtrail put-event-selectors \
  --trail-name fyp-poc-trail --region us-east-1 \
  --event-selectors '[{"ReadWriteType":"All","IncludeManagementEvents":true,"DataResources":[{"Type":"AWS::S3::Object","Values":["arn:aws:s3:::fyp-persistence-test/"]}]}]'

# Describe trail configuration
aws --endpoint-url=http://localhost:4567 cloudtrail describe-trails --region us-east-1
```
> **Evidence (SS-04 - CloudTrail Trail Configuration):**  
> ![SS-04: CloudTrail Trail Config](evidences/04-cloudtrail-trail-config.png)

```bash
# Check trail logging status
aws --endpoint-url=http://localhost:4567 cloudtrail get-trail-status --name fyp-poc-trail --region us-east-1
```
> **Evidence (SS-05 - CloudTrail Logging Enabled):**  
> ![SS-05: CloudTrail Logging Enabled](evidences/05-cloudtrail-logging-enabled.png)

### 4.4 CloudTrail Log Sync & Inspection
```bash
aws --endpoint-url=http://localhost:4567 s3 sync s3://fyp-persistence-test/AWSLogs/ poc-data/cloudtrail-logs/AWSLogs/
python scripts/inspect_cloudtrail.py
```
> **Evidence (SS-08 - CloudTrail GetObject Events):**  
> ![SS-08: CloudTrail GetObject Events](evidences/08-cloudtrail-getobject-events.png)

---

## 5. Test Results & Observed Evidence

### 5.1 CloudTrail Object Access Events
`scripts/inspect_cloudtrail.py` verified three matching `GetObject` events for `synthetic/test-data.txt`:

| Event Time (UTC) | Action | Resource | Identity | Error |
| :--- | :--- | :--- | :--- | :--- |
| `2026-10-20T12:54:47Z` | `GetObject` | `fyp-persistence-test / synthetic/test-data.txt` | `arn:aws:iam::000000000000:root` | `None` |
| `2026-10-20T13:08:15Z` | `GetObject` | `fyp-persistence-test / synthetic/test-data.txt` | `arn:aws:iam::000000000000:root` | `None` |
| `2026-10-20T13:23:04Z` | `GetObject` | `fyp-persistence-test / synthetic/test-data.txt` | `arn:aws:iam::000000000000:root` | `None` *(post-restart)* |

### 5.2 Agent-to-Receiver Transfer

| Metric | Agent (`agent-runs.jsonl`) | Receiver (`transfers.jsonl`) |
| :--- | :--- | :--- |
| **Run ID / Status** | `20261020T130815222751Z` / `200 accepted` | Request accepted (`POST /transfer`) |
| **Bytes Transferred** | 75 bytes | 75 bytes |
| **Payload Hash** | `1819059edc21d93eebbe0c452a51a6d6d43923833c3140a5f9939f36b5aa5276` | `1819059edc21d93eebbe0c452a51a6d6d43923833c3140a5f9939f36b5aa5276` |

*Integrity verified:* Exact byte size and SHA-256 match confirmed across agent transmission and receiver reception.

> **Evidence (SS-06 - Agent Run Success):**  
> ![SS-06: Agent Success](evidences/06-agent-success.png)

> **Evidence (SS-07 - Receiver Hash Match):**  
> ![SS-07: Receiver Hash Match](evidences/07-receiver-hash-match.png)

### 5.3 Persistence Verification (Container Restart)
Execute container restart:
```bash
docker restart floci-persistent
```
> **Evidence (SS-09 - Persistence After Restart):**  
> ![SS-09: Persistence After Restart](evidences/09-persistence-after-restart.png)

Post-restart verification and log sync:
```bash
# Sync logs after post-restart object access
aws --endpoint-url=http://localhost:4567 s3 sync s3://fyp-persistence-test/AWSLogs/ poc-data/cloudtrail-logs/AWSLogs/
python scripts/inspect_cloudtrail.py
```
> **Evidence (SS-10 - Post-Restart Log Sync & Verification):**  
> ![SS-10: Post-Restart Log Sync](evidences/10-post-restart-log-sync.png)

1. **API Reachability:** STS caller identity responded immediately after restart.
2. **Trail Configuration:** `fyp-poc-trail` remained configured and active (`IsLogging: true`).
3. **Data & Audit Persistence:** Historical logs remained accessible; new post-restart access (`13:23:04Z`) was captured and synced successfully.

---

## 6. Evidence & Screenshot Checklist

All screenshot evidence is stored in `docs/poc/evidences/` and embedded under the corresponding command/section:

| ID | Filename | Description | Location in Document | Priority |
| :--- | :--- | :--- | :--- | :--- |
| **SS-01** | `01-floci-container-volume.png` | Container & volume in Docker / terminal | [Section 2.1](#21-floci-container--volume-setup) | Recommended |
| **SS-02** | `02-floci-api-identity.png` | `sts get-caller-identity` output | [Section 4.1](#41-verify-sts-identity) | **Core** |
| **SS-03** | `03-synthetic-s3-object.png` | S3 `get-object` showing 75-byte length | [Section 4.2](#42-verify-s3-object-retrieval) | Optional |
| **SS-04** | `04-cloudtrail-trail-config.png` | `describe-trails` output | [Section 4.3](#43-configure--verify-cloudtrail) | **Core** |
| **SS-05** | `05-cloudtrail-logging-enabled.png` | `get-trail-status` showing `IsLogging: true` | [Section 4.3](#43-configure--verify-cloudtrail) | **Core** |
| **SS-06** | `06-agent-success.png` | Agent run log (75 bytes, HTTP 200) | [Section 5.2](#52-agent-to-receiver-transfer) | **Core** |
| **SS-07** | `07-receiver-hash-match.png` | Receiver JSONL log with matching SHA-256 | [Section 5.2](#52-agent-to-receiver-transfer) | **Core** |
| **SS-08** | `08-cloudtrail-getobject-events.png` | Inspector output with 3 `GetObject` events | [Section 4.4](#44-cloudtrail-log-sync--inspection) | **Core** |
| **SS-09** | `09-persistence-after-restart.png` | `docker restart` + active trail status | [Section 5.3](#53-persistence-verification-container-restart) | **Core** |
| **SS-10** | `10-post-restart-log-sync.png` | S3 sync showing logs after restart | [Section 5.3](#53-persistence-verification-container-restart) | Optional |

---

## 7. Validation Checklist

- [x] Persistent Floci API operational on port 4567
- [x] Synthetic S3 object present and retrievable (75 bytes)
- [x] CloudTrail trail configured with S3 data events
- [x] Trail actively logging (`IsLogging: true`)
- [x] `GetObject` audit events generated in CloudTrail logs
- [x] Python agent retrieves payload and delivers to receiver
- [x] Payload SHA-256 hash verified identically at receiver
- [x] Container restart preserves configuration and historical data
- [x] New post-restart access events captured and delivered

---

## 8. Next Steps & Operating Notes

1. **Experimental Baseline:** Retain container `floci-persistent` and volume `floci-persistent-data` without changes.
2. **Scenarios & Ground Truth:** Formalize benign, overt-exfiltration, and low-volume exfiltration specifications.
3. **Evidence Degradation:** Develop and benchmark degraded audit transformations (dropped events, delayed logs).
4. **Detector Evaluation:** Build normalized detector inputs and evaluate 4 monitoring strategies across 520 test runs.
5. **Timezone Reference:** Audit logs use UTC (`Z`); CLI local timestamps use MYT (`+08:00`). Convert prior to analysis.
