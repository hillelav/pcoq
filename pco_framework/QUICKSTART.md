# PCO Framework - Quick Start Guide

## What is PCO?

**PCO (Provably Compliant Outcomes)** - A framework where AI systems must prove their outputs comply with formal regulatory specifications BEFORE acting.

## Installation (2 minutes)

```bash
cd /Users/hillelavni/Documents/project/pcoq_trunk/pcoq/pco_framework

# Install dependencies (choose one or both)
pip install anthropic  # For Claude API (recommended)
pip install openai     # For OpenAI API

# Install Coq
brew install coq

# Set API key (choose one)
export ANTHROPIC_API_KEY="sk-ant-your-key"
# OR
export OPENAI_API_KEY="sk-your-key"
```

## Run Dashboard (1 command)

```bash
./run.sh
```

Or:

```bash
python3 dashboard.py
```

## 5-Minute Demo

### Step 1: Launch Dashboard

```bash
python3 dashboard.py
```

### Step 2: Select Use Case

From the dropdown, choose one of:
- **tax_compliance** - IRS tax computation verification
- **autonomous_vehicle** - AV safety compliance
- **consumer_protection** - Recommendation system fairness

### Step 3: View Prompt (Optional)

Click **"View Prompt"** to see the full specification that will be sent to the LLM.

### Step 4: Execute Pipeline

1. Enter your OpenAI API key (or set environment variable)
2. Select verifier (default: **coqc**)
3. Click **"Execute (Generate & Verify)"**

**What happens:**
- LLM generates complete Coq proof
- Saves to `pco_storage/[usecase]_[timestamp].v`
- Runs verifier automatically
- Shows output: **PASS** ✓ or **FAIL** ✗

### Step 5: Record to Blockchain (if PASS)

1. If verification passed, **"Record to Blockchain"** button becomes active
2. Click it
3. Proof hash is computed: `SHA256(proof + proposition)`
4. Record stored in `pco_storage/blockchain.json` with:
   - Timestamp
   - Hash
   - Proof file location
   - Verification status

## Example Output

```
======================================================================
PCO Pipeline: tax_compliance
======================================================================

Step 1: Generating Coq proof from LLM...
✓ Generated Coq code (3421 chars)
✓ Proposition: tax_compliant_computation
✓ Saved to: pco_storage/tax_compliance_20260112_143022.v

Step 2: Verifying with coqc...
Verifier output:
[coqc output...]

======================================================================
✅ VERIFICATION: PASS
======================================================================

Step 3: Recording to Blockchain
======================================================================

✓ Hash: a1b2c3d4e5f6789...
✓ Timestamp: 2026-01-12T14:30:22.123456
✓ Proof file: pco_storage/tax_compliance_20260112_143022.v

✅ Successfully recorded to blockchain!
```

## Blockchain Structure

All records stored in `pco_storage/blockchain.json`:

```json
[
  {
    "timestamp": "2026-01-12T14:30:22.123456",
    "use_case": "tax_compliance",
    "proposition": "tax_compliant_computation",
    "verifier": "coqc",
    "hash": "a1b2c3d4e5f6...",
    "proof_file": "pco_storage/tax_compliance_20260112_143022.v",
    "verification_status": "PASS"
  }
]
```

## Auditing

To audit a proof:

```python
# audit.py
import hashlib
import json

# Load blockchain
with open("pco_storage/blockchain.json") as f:
    blockchain = json.load(f)

# Select record
record = blockchain[0]

# Recompute hash
with open(record["proof_file"]) as f:
    proof = f.read()
combined = f"{proof}|||{record['proposition']}"
computed_hash = hashlib.sha256(combined.encode()).hexdigest()

# Compare
if computed_hash == record["hash"]:
    print("✓ AUDIT: PASS")
else:
    print("✗ AUDIT: FAIL - Proof was modified")
```

## Files Generated

Each execution creates:
- **Coq proof file**: `pco_storage/{usecase}_{timestamp}.v`
- **Blockchain record**: Updated `pco_storage/blockchain.json`

## Use Cases in Detail

### Tax Compliance
- **Input**: Income, deductions, filing status
- **Output**: Tax owed
- **Proof**: Computed tax matches IRS specification
- **Authority**: IRS publishes TaxLaw.v

### Autonomous Vehicle
- **Input**: Sensor data (speed, position, obstacles)
- **Output**: Driving action (accelerate, brake, steer)
- **Proof**: Action is safe given current state
- **Authority**: Transportation Ministry publishes SafetySpec.v

### Consumer Protection
- **Input**: User preferences, product catalog
- **Output**: Product recommendation
- **Proof**: Recommendation maximizes utility, no manipulation
- **Authority**: Consumer Protection Agency publishes FairRankingSpec.v

## Troubleshooting

### "Module 'openai' not found"
```bash
pip install openai
```

### "coqc: command not found"
```bash
brew install coq
# Or download from https://coq.inria.fr/
```

### "Authentication error"
- Check OPENAI_API_KEY is set correctly
- Verify key is valid (not expired)

### "Verification fails"
- LLM may generate incorrect code
- Try clicking "Execute" again
- Or manually edit the .v file

## Advanced: Manual Verification

You can manually verify any generated proof:

```bash
cd pco_storage
coqc tax_compliance_20260112_143022.v
```

## Security Model

1. **Proof Authenticity**: SHA-256 hash ensures proof wasn't modified
2. **Timestamp**: Proves when verification occurred
3. **Immutability**: Blockchain records are append-only
4. **Transparency**: All proofs stored locally for inspection

## Next Steps

- Add audit interface to dashboard
- Integrate with real blockchain (Ethereum/Hyperledger)
- Support multi-file Coq projects
- Add proof templates for common patterns
