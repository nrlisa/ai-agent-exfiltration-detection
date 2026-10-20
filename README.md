# AI Agent Exfiltration Detection

A project dedicated to detecting, analyzing, and mitigating data exfiltration vectors originating from autonomous and semi-autonomous AI agents.

## Project Structure

```text
ai-agent-exfiltration-detection/
├── docs/
│   ├── architecture/       # System design, data flow, and threat modeling
│   ├── methodology/        # Detection methodologies and heuristics
│   └── poc/                # Proof of concept reports, logs, and evidence
│       ├── commands.md     # Command line reference for reproducing PoCs
│       ├── evidence/       # Artifacts, test run captures, and sample outputs
│       │   ├── environment.png
│       │   ├── sample-output.json
│       │   └── test-results.png
│       └── poc-report.md   # Detailed PoC report and findings
├── src/                    # Detection engine, monitors, and agent telemetry analyzers
├── tests/                  # Unit and integration test suites
└── README.md
```

## Getting Started

### Prerequisites
- Python 3.10+ / Node.js 18+ (depending on runtime components)
- Required dependencies (to be placed in `requirements.txt` or `package.json` in `src/`)

### Running Detection Tests
Refer to [commands.md](file:///C:/Users/USER/Downloads/ai-agent-exfiltration-detection/docs/poc/commands.md) for instructions on executing test harnesses and viewing detection alerts.
