# PCO Framework - Provably Compliant Outcomes

## Overview

The PCO Framework automates the generation, verification, and recording of regulatory compliance proofs using:
1. **LLM Integration** - Generates Coq proofs from regulatory prompts
2. **Automated Verification** - Runs Coq verifiers (coqc, rcoq, coqide)
3. **Blockchain Recording** - Stores proof hashes with timestamps

## Three Use Cases

### 1. Tax Compliance (IRS Auditing)
- Formalizes tax brackets, deductions, filing statuses
- Proves computed tax matches specification
- All amounts in cents to avoid floating point errors

### 2. Autonomous Vehicle Safety
- Hybrid STL+Coq verification architecture
- Real-time STL monitors (<1ms)
- Post-hoc Coq proofs from logged data
- Cryptographic signatures on all sensor inputs

### 3. Consumer Protection (Recommendations)
- Proves recommendations maximize user utility
- No hidden manipulation
- Full disclosure of commercial relationships
- Optimality guarantees

## Installation

```bash
cd /Users/hillelavni/Documents/project/pcoq_trunk/pcoq/pco_framework

# Install dependencies (choose one or both)
pip install anthropic  # For Claude API (recommended)
pip install openai     # For OpenAI API

# For verification
brew install coq

# Set API key (choose one)
export ANTHROPIC_API_KEY="sk-ant-api03-your-key"
# OR
export OPENAI_API_KEY="sk-your-key"

# Run diagnostics to verify setup
python3 diagnose_api.py
```

## ⚠️ Getting API Errors?

If you see "No available Claude models found" or similar errors:

```bash
# Run comprehensive diagnostics
python3 diagnose_api.py

# This will show exactly what's wrong and how to fix it
```

See `API_ISSUES.md` for detailed troubleshooting.

## Usage

### Quick Start

```bash
python3 dashboard.py
```

### Workflow

1. **Select Use Case**
   - Choose from: tax_compliance, autonomous_vehicle, consumer_protection
   - Click "View Prompt" to see the full specification

2. **Configure**
   - Select verifier (coqc, rcoq, or coqide)
   - Enter OpenAI API key (or set OPENAI_API_KEY env var)

3. **Execute**
   - Click "Execute (Generate & Verify)"
   - LLM generates Coq proof from prompt
   - Verifier checks proof automatically
   - Result: PASS ✓ or FAIL ✗

4. **Record** (only if PASS)
   - Click "Record to Blockchain"
   - Computes SHA-256 hash of proof + proposition
   - Stores in blockchain.json with timestamp
   - Saves proof file to pco_storage/

## Architecture

```
┌─────────────────────────────────────────┐
│           User selects use case         │
├─────────────────────────────────────────┤
│  1. Tax Compliance                      │
│  2. Autonomous Vehicle Safety           │
│  3. Consumer Protection                 │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│      Generate Coq Proof via LLM         │
│  (OpenAI GPT-4 API)                     │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│      Verify with Coq Verifier           │
│  (coqc / rcoq / coqide)                 │
└──────────────┬──────────────────────────┘
               ↓
         PASS or FAIL?
               ↓
         [If PASS]
┌─────────────────────────────────────────┐
│     Record to Blockchain                │
│  - Hash = SHA256(proof + proposition)   │
│  - Timestamp                            │
│  - Store proof file locally             │
└─────────────────────────────────────────┘
```

## File Structure

```
pco_framework/
├── dashboard.py           # Main GUI application
├── README.md             # This file
├── run.sh                # Quick start script
└── pco_storage/          # Generated proofs & blockchain
    ├── blockchain.json   # Blockchain records
    ├── tax_compliance_20260112_143022.v
    ├── autonomous_vehicle_20260112_143155.v
    └── consumer_protection_20260112_143301.v
```

## Blockchain Format

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

## Example Session

```
1. Launch: python3 dashboard.py

2. Select "tax_compliance" from dropdown

3. Click "View Prompt" to see:
   - Tax bracket specifications
   - Filing status types
   - Progressive tax computation
   
4. Click "Execute":
   → LLM generates TaxCompliance.v
   → coqc verifies proof
   → Output: PASS ✓
   
5. Click "Record to Blockchain":
   → Hash: a1b2c3...
   → Timestamp: 2026-01-12T14:30:22
   → Saved to blockchain.json
```

## Extending

To add a new regulatory domain:

1. Add prompt to `PCO_PROMPTS` dict in `dashboard.py`
2. Follow the template structure:
   - Domain types (Inductive, Record)
   - Core computations (Definition)
   - THE COMPLIANCE PREDICATE
   - Signature verification
   - Example proof

## Troubleshooting

### "openai module not found"
```bash
pip install openai
```

### "coqc not found"
```bash
brew install coq
```

### "API key error"
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# Or
export OPENAI_API_KEY="sk-..."
# Or enter in GUI
```

### "Model not found" (404 error)
The dashboard automatically tries multiple Claude model versions. Test with:
```bash
python3 test_claude_api.py
```

See `CLAUDE_MODELS.md` for detailed model information.

### "Verification fails"
- The LLM-generated proof may have errors
- Click "Execute" again to regenerate
- Or manually edit the .v file in pco_storage/

### More Help
- `TROUBLESHOOTING.md` - Complete troubleshooting guide
- `CLAUDE_MODELS.md` - Claude model reference
- `SETUP_CLAUDE.md` - Claude-specific setup

## Security Notes

- API keys are stored in memory only (not saved to disk)
- Blockchain is local JSON (can be upgraded to real blockchain)
- Proof files are stored locally in pco_storage/
- Hashes use SHA-256 (cryptographically secure)

## Future Enhancements

- [ ] Integration with real blockchain (Ethereum, Hyperledger)
- [ ] Multi-file Coq project support
- [ ] Proof search/audit interface
- [ ] Automated proof repair suggestions
- [ ] Export compliance certificates (PDF)

## License

MIT License
