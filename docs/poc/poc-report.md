# Proof of Concept (PoC) Report

## 1. Purpose

The purpose of this proof of concept (PoC) was to assess the technical feasibility of using a local cloud-emulation environment for the proposed AI-Agent Data Exfiltration Detection Framework.

The PoC focused on validating the required environment and testing the relevant cloud-storage operations through an SDK. This preliminary test was intended to identify potential implementation issues before developing the monitoring strategies and conducting the main experiment.

## 2. Test Environment

| Component | Configuration |
|---|---|
| Operating system | Windows |
| Container platform | Docker Desktop |
| Cloud emulator | Floci |
| Programming language | Python |
| AWS SDK | boto3 |
| Endpoint | Local emulator endpoint |
| Test scope | Initial technical feasibility |

*Note: Record the actual versions and configurations used during the test.*

## 3. Test Procedure

### 3.1 Environment Startup

The cloud-emulation environment was started using Docker. The service status was checked to determine whether the environment was running and ready for subsequent testing.

**Expected result:** The service starts successfully and becomes available.

**Actual result:** [Record the actual outcome.]

**Evidence:** Figure 1 — Environment startup verification.

### 3.2 Cloud Storage Operation

A cloud-storage operation was performed against the local emulator using the relevant AWS-compatible interface.

The test was intended to determine whether the required storage operation could be performed within the local test environment.

**Expected result:** The requested operation completes successfully.

**Actual result:** [Record the actual outcome.]

**Evidence:** Figure 2 — Successful storage operation.

### 3.3 SDK Integration

The boto3 SDK was used to communicate with the local cloud-emulation endpoint.

The test examined whether the SDK could issue the required request and receive an appropriate response.

**Expected result:** The request completes and returns the expected response.

**Actual result:** [Record the actual outcome.]

**Evidence:** Figure 3 — SDK integration test output.

### 3.4 Audit Evidence Verification

The available output or event records were examined to determine whether the information required by the proposed monitoring framework could be obtained.

The inspection focused on the availability of relevant information, such as the operation performed, resource identifier, timestamp and identity information.

**Expected result:** The required evidence is available through the tested logging mechanism or can be obtained through a separately validated mechanism.

**Actual result:** [Record exactly which evidence was available and which fields were missing or not tested.]

**Evidence:** Figure 4 — Audit evidence inspection, if applicable.

## 4. Summary of Results

| Test | Result | Observation |
|---|---|---|
| Environment startup | [Pass/Fail] | [Actual observation] |
| Storage operation | [Pass/Fail/Not tested] | [Actual observation] |
| SDK integration | [Pass/Fail/Not tested] | [Actual observation] |
| Audit evidence verification | [Pass/Fail/Partial/Not tested] | [Actual observation] |

## 5. Limitations

This PoC was limited to preliminary technical validation. It did not, by itself, establish the effectiveness of the proposed monitoring strategies.

Any unverified functionality, including audit-event generation, event correlation, outbound-transfer observation and detection performance, requires separate testing.

## 6. Conclusion

The PoC provided preliminary evidence regarding the feasibility of the selected local test environment.

Based on the tests completed, the following components were [validated / partially validated / not yet validated]: [list actual findings].

The results will inform the next implementation stage, which involves developing the controlled scenarios, preparing the evidence inputs and implementing the four monitoring strategies for comparative evaluation.
