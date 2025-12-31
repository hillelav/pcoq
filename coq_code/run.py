#!/usr/bin/env python3
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

DOMAINS = {
    "recommendation": [
        "UserPreference.v",
        "ProductSpec.v",
        "DisclosureSpec.v",
        "FairRankingSpec.v",
        "RecommendationComplianceSpec.v",
        "RecommendationProof_Example.v",
        "AuditSpec.v",
    ],
    "tax": [
        "TaxCode.v",
        "DocumentSpec.v",      # ← must come before ComputeSpec
        "ComputeSpec.v",
        "TaxProof_Example.v",
    ],
    "traffic": [
        "TrafficLaw.v",
        "SafetySpec.v",
        "ComplianceSpec.v",
        "ComplianceProof_Example.v",
    ],
}

def run(cmd):
    print(f"    ▶ {cmd}")
    subprocess.check_call(cmd, shell=True)

print("🧠 PCoq: compiling all specs & proofs\n")

for domain, files in DOMAINS.items():
    print(f"\n📂 Compiling {domain}")
    domain_dir = os.path.join(ROOT, domain)
    os.chdir(domain_dir)

    # Clean local build artifacts
    run("rm -f *.vo *.vos *.vok *.glob")

    for f in files:
        run(f"coqc {f}")

print("\n✅ All PCoq domains compiled successfully")

