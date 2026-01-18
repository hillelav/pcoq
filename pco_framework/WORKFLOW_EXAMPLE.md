# PCO Framework - Complete Workflow Example

## Scenario: Verifying Tax Compliance

This example demonstrates the complete PCO workflow from prompt to blockchain recording.

## Setup

```bash
cd /Users/hillelavni/Documents/project/pcoq_trunk/pcoq/pco_framework

# Install dependencies
pip install openai
brew install coq

# Set API key
export OPENAI_API_KEY="sk-your-openai-key"
```

## Step-by-Step Workflow

### 1. Launch Dashboard

```bash
python3 dashboard.py
```

### 2. Configure

In the dashboard GUI:
- **Use Case**: Select "tax_compliance"
- **Verifier**: Select "coqc"
- **API Key**: Automatically loaded from environment (or enter manually)

### 3. View Prompt (Optional)

Click **"View Prompt"** to see:

```
Create a Coq specification for IRS tax computation that formalizes:
- Filing status types (Single, MarriedFilingJointly, etc.)
- 2024 tax brackets with exact thresholds from Rev. Proc. 2023-34
- Standard deductions by filing status
- Progressive tax computation with bracket_tax helper
...
```

### 4. Execute Pipeline

Click **"Execute (Generate & Verify)"**

**What happens internally:**

```
Dashboard → OpenAI API (with prompt)
         ↓
    LLM generates Coq code:
         ↓
    Inductive FilingStatus := Single | MarriedJoint | ...
    Definition standard_deduction := ...
    Definition compute_tax := ...
    Theorem tax_compliant_computation : ...
    Proof. ... Qed.
         ↓
    Save to: pco_storage/tax_compliance_20260112_143022.v
         ↓
    Run: coqc pco_storage/tax_compliance_20260112_143022.v
         ↓
    Result: PASS ✓ or FAIL ✗
```

**Output in dashboard:**

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
[coqc successfully compiled]

======================================================================
✅ VERIFICATION: PASS
======================================================================
```

**Popup message:** "PASS ✓ Proof is valid!"

### 5. Record to Blockchain

1. **"Record to Blockchain"** button is now enabled (green)
2. Click it

**What happens:**

```
Read: pco_storage/tax_compliance_20260112_143022.v
Compute: SHA256(proof_content + "|||" + "tax_compliant_computation")
Hash: a1b2c3d4e5f6789...
Store in blockchain.json:
  {
    "timestamp": "2026-01-12T14:30:22.123456",
    "use_case": "tax_compliance",
    "proposition": "tax_compliant_computation",
    "verifier": "coqc",
    "hash": "a1b2c3d4e5f6...",
    "proof_file": "pco_storage/tax_compliance_20260112_143022.v",
    "verification_status": "PASS"
  }
```

**Output:**

```
✓ Hash: a1b2c3d4e5f6789...
✓ Timestamp: 2026-01-12T14:30:22.123456
✓ Proof file: pco_storage/tax_compliance_20260112_143022.v

✅ Successfully recorded to blockchain!
```

**Popup:** "Proof recorded to blockchain! Hash: a1b2c3..."

### 6. Audit (Later)

Run the audit tool to verify all blockchain records:

```bash
python3 audit.py
```

**Output:**

```
======================================================================
PCO Audit Tool
======================================================================

Found 1 blockchain record(s)

Record 1/1:
  Timestamp:   2026-01-12T14:30:22.123456
  Use Case:    tax_compliance
  Proposition: tax_compliant_computation
  Verifier:    coqc
  Hash:        a1b2c3d4e5f6...
  ✓ AUDIT: PASS

======================================================================
Audit Summary
======================================================================
Total:  1
Passed: 1 ✓
Failed: 0 ✗

✅ All proofs are authentic!
```

## Complete Example: All Three Use Cases

```bash
# 1. Tax Compliance
python3 dashboard.py
# → Select "tax_compliance"
# → Execute → PASS
# → Record

# 2. Autonomous Vehicle
python3 dashboard.py
# → Select "autonomous_vehicle"
# → Execute → PASS
# → Record

# 3. Consumer Protection
python3 dashboard.py
# → Select "consumer_protection"
# → Execute → PASS
# → Record

# Audit all
python3 audit.py
# → Shows 3 records, all PASS
```

## File Structure After Execution

```
pco_framework/
├── dashboard.py
├── audit.py
├── run.sh
├── README.md
├── QUICKSTART.md
├── requirements.txt
└── pco_storage/
    ├── blockchain.json                           # Blockchain records
    ├── tax_compliance_20260112_143022.v         # Tax proof
    ├── autonomous_vehicle_20260112_143155.v     # AV proof
    └── consumer_protection_20260112_143301.v    # Recommendation proof
```

## What Makes This Secure?

1. **Cryptographic Hash**: SHA-256 ensures tamper detection
2. **Timestamp**: Proves when verification occurred
3. **Immutable Log**: Blockchain records are append-only
4. **Source Preservation**: Original proof files stored
5. **Reproducible**: Anyone can re-verify the proof

## Real-World Usage

In production:
- AI system generates output (tax computation, driving decision, recommendation)
- System calls PCO framework to generate compliance proof
- Proof is verified before action is taken
- Hash recorded on blockchain for audit trail
- Regulators can audit anytime by checking hashes

## Next Steps

- Integrate with real blockchain (Ethereum, Hyperledger)
- Add web interface (Flask/FastAPI)
- Create CI/CD pipeline for automated verification
- Build regulatory compliance dashboard
