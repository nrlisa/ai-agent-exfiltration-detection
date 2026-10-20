# PoC Execution Commands

Reference commands for reproducing the detection test suite and generating evidence artifacts.

## 1. Setup Environment

```bash
# Clone or navigate to the repository
cd ai-agent-exfiltration-detection

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1

# Install dependencies (once added to src/)
pip install -r src/requirements.txt
```

## 2. Running the Detection Harness

```bash
# Execute unit and detection scenario tests
pytest tests/ -v

# Run the agent monitor simulation
python src/main.py --mode monitor --target-agent mock-agent-01
```

## 3. Capturing Output & Evidence

```bash
# Run simulation with JSON alert output
python src/main.py --simulate-exfil --output docs/poc/evidence/sample-output.json
```
