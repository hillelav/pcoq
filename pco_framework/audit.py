#!/usr/bin/env python3
"""
PCO Audit Tool - Verify blockchain records
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime


def load_blockchain():
    """Load blockchain records"""
    blockchain_file = Path("pco_storage/blockchain.json")
    if blockchain_file.exists():
        with open(blockchain_file, 'r') as f:
            return json.load(f)
    return []


def audit_record(record):
    """
    Audit a single blockchain record.
    Returns: (status, message) where status is 'PASS' or 'FAIL'
    """
    try:
        # Read proof file
        proof_file = Path(record["proof_file"])
        if not proof_file.exists():
            return "FAIL", f"Proof file not found: {proof_file}"
        
        with open(proof_file, 'r') as f:
            proof_content = f.read()
        
        # Recompute hash
        combined = f"{proof_content}|||{record['proposition']}"
        computed_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        # Compare
        if computed_hash == record['hash']:
            return "PASS", "Hash matches - proof is authentic"
        else:
            return "FAIL", f"Hash mismatch!\n  Stored:   {record['hash']}\n  Computed: {computed_hash}"
    
    except Exception as e:
        return "FAIL", f"Error: {e}"


def main():
    print()
    print("=" * 70)
    print("PCO Audit Tool")
    print("=" * 70)
    print()
    
    blockchain = load_blockchain()
    
    if not blockchain:
        print("No blockchain records found.")
        print("Run dashboard.py to generate and verify proofs first.")
        return
    
    print(f"Found {len(blockchain)} blockchain record(s)")
    print()
    
    # Audit each record
    pass_count = 0
    fail_count = 0
    
    for i, record in enumerate(blockchain, 1):
        print(f"Record {i}/{len(blockchain)}:")
        print(f"  Timestamp:   {record['timestamp']}")
        print(f"  Use Case:    {record['use_case']}")
        print(f"  Proposition: {record['proposition']}")
        print(f"  Verifier:    {record['verifier']}")
        print(f"  Hash:        {record['hash'][:32]}...")
        
        status, message = audit_record(record)
        
        if status == "PASS":
            print(f"  ✓ AUDIT: {status}")
            pass_count += 1
        else:
            print(f"  ✗ AUDIT: {status}")
            print(f"  {message}")
            fail_count += 1
        
        print()
    
    # Summary
    print("=" * 70)
    print("Audit Summary")
    print("=" * 70)
    print(f"Total:  {len(blockchain)}")
    print(f"Passed: {pass_count} ✓")
    print(f"Failed: {fail_count} ✗")
    print()
    
    if fail_count == 0:
        print("✅ All proofs are authentic!")
    else:
        print("⚠️  Some proofs have been modified!")


if __name__ == "__main__":
    main()
