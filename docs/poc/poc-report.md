# Floci Proof of Concept (PoC) Documentation

**Project:** AI-Agent Data Exfiltration Detection Framework  
**FYP Title:** Design and Evaluation of Monitoring Strategies for Detecting AI-Agent Data Exfiltration under Incomplete Cloud Audit Evidence  
**Status:** FYP1 M1 PoC evidence consolidated; M1 gate remains conditional pending detector-input connection
**Updated:** 27 October 2026 | **Environment:** Windows, Git Bash, Docker, AWS CLI, Python/boto3

---

## 1. Purpose & Scope

This report records the FYP1 M1 feasibility PoC for the local cloud-emulation testbed (Floci):
- S3-compatible synthetic data storage and retrieval (AWS CLI & Python/boto3 agent).
- CloudTrail-format audit event generation and delivery for object-level access.
- Exfiltration to a local HTTP receiver with SHA-256 integrity verification.
- State and audit log persistence across container restarts.

> **M1 scope:** This is a local synthetic-data PoC. It checks that storage, audit evidence, and outbound transfer can be demonstrated and identifies whether the baseline is feasible. It does not evaluate monitoring strategies or claim the full FYP system is complete. The Gantt's FYP1 M1 gate also calls for detector input to be connected; that connection is not yet evidenced below.

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

CloudTrail records are synced to local compressed JSON files and inspected with `scripts/inspect_cloudtrail.py`. The current repository demonstrates event inspection and agent-to-receiver transfer as separate outputs; it does not yet demonstrate an audit event entering a detector-input interface.

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
python scripts/inspect_cloudtrail.py --target old-poc
```
Use `--target experiment` (the default) for the experiment bucket. The older screenshots and event table in this report refer to the `old-poc` target.

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

The committed experiment logs also contain a 27 October 2026 run with a 75-byte payload, HTTP 200 response, and matching SHA-256 at the receiver. The repository contains two agent-run records and three receiver records overall; these logs do not share a common run ID, so they do not establish one-to-one joins for every transfer and CloudTrail event.

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

## 7. FYP1 M1 Checklist and Feasibility Assessment

The project Gantt places FYP1 M1 at W4 and names the deliverable “PoC checklist and evidence.” Its gate is a proof of concept connecting cloud storage, audit evidence, receiver, and detector input. Status below is based on the evidence committed in this repository; it does not imply that the local services were re-run during this report update.

| M1 acceptance item | Status | Evidence / remaining work |
| :--- | :--- | :--- |
| Local Floci environment and persistent state demonstrated | Evidence recorded | SS-01, SS-02, SS-09, and SS-10 document the container, API identity, restart, and post-restart state. |
| Synthetic S3 object is available and retrievable | Evidence recorded | SS-03 documents the 75-byte object retrieval. |
| CloudTrail object-level logging and `GetObject` evidence demonstrated | Evidence recorded | SS-04 and SS-05 document trail configuration and logging status; SS-08 and Section 5.1 record matching object-read events. |
| Outbound receiver accepts the agent payload and verifies integrity | Evidence recorded | SS-06 and SS-07 document the 75-byte transfer, HTTP success, and matching SHA-256. A later experiment run is also present in the committed JSONL logs. |
| Shared detector-input boundary is demonstrated | **Open — M1 gate not yet met** | The inspector currently prints matching events. No detector-input interface or handoff is present in the checked-in implementation/evidence. Demonstrate one bounded baseline input consistent with the shared contract: verified audit evidence, raw outbound-activity metadata, and shared destination policy. Detector logic and scenario automation are not required for this M1 item. |
| M1 checklist and feasibility assessment recorded | Recorded here; team sign-off pending | See the assessment below. |

### Feasibility decision

**Repository-based assessment: conditional GO for the scoped local PoC baseline; do not mark the M1 gate complete yet.** The committed evidence supports the feasibility of using Floci to store and retrieve synthetic data, produce and inspect CloudTrail-format object-read events, and demonstrate a local agent-to-receiver transfer with matching payload hashes. The remaining M1 condition is to demonstrate one bounded baseline input at the shared detector-input boundary and attach that evidence to this checklist.

This is a feasibility assessment, not evidence that detection effectiveness has been evaluated. The current evidence is limited to a local emulator, synthetic payloads, and a small PoC record set. It does not establish real-cloud behavior, completed monitoring strategies, scenario coverage, or experiment results. This assessment does not change the approved research question, fixed scripted-agent role, three scenarios, two evidence conditions, four monitoring strategies, or planned 520-run matrix. The enhanced LLM specification remains a monitor design; this PoC does not claim it is implemented. The assessment should be reviewed and signed off by the project team after the open checklist item is closed.

### M1 close-out actions

1. Connect one bounded baseline input consistent with the shared contract: a verified CloudTrail event, raw outbound-activity metadata, and the shared destination policy. Use the complete baseline evidence condition for this demonstration.
2. Keep the input free of scenario labels, receiver ground truth, and evaluation-manifest data. Capture the input and its source evidence, preserving provenance and avoiding claims of a complete run-level join where the current logs have no shared run ID.
3. Recheck the checklist statuses against that evidence and record the team's M1 feasibility decision/sign-off.

These actions close the M1 gate only; this report does not treat later milestone work as an M1 requirement.

### Operating note

Audit event timestamps use UTC (`Z`). Convert local CLI timestamps from MYT (`+08:00`) before comparing event times.
