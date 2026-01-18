#!/usr/bin/env python3
"""
PCO Framework Dashboard
Generates Coq proofs from regulatory compliance prompts using LLM,
verifies them, and records on blockchain.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import hashlib
import json
import subprocess
from datetime import datetime
from pathlib import Path
import os

# PCO Use Case Prompts
PCO_PROMPTS = {
    "tax_compliance": """Create a Coq specification for IRS tax computation that formalizes:
- Filing status types (Single, MarriedFilingJointly, etc.)
- 2024 tax brackets with exact thresholds from Rev. Proc. 2023-34
- Standard deductions by filing status
- Progressive tax computation with bracket_tax helper
- Verification lemmas (tax_nonneg, tax_monotonic)

The IRS (hypothetically) publishes this as the authoritative tax code specification.

Key design decisions:
• All amounts in cents (Z type) to avoid floating point
• IRC section citations in comments
• Decidable bracket computation with let bindings

Required files:
1. TaxLaw.v - Tax brackets, filing statuses, deductions
2. TaxComputation.v - Progressive tax calculation formulas
3. SignatureSpec.v - Cryptographic validation of tax documents
4. TaxComplianceSpec.v - Main compliance predicate combining:
   - inputs_certified (all signatures valid)
   - income >= 0
   - deductions <= max_deductions(filing_status)
   - compute_tax(return) = tax_owed

Generate complete working Coq code with example proof.""",

    "autonomous_vehicle": """Create a hybrid verification architecture for AV compliance where:
- Real-time: STL monitors verify safety in <1ms (phi_speed, phi_following, phi_lane, phi_signal)
- Audit: Coq proofs reconstruct from logged data post-hoc

The Transportation Ministry publishes:
1. TrafficLaw.v - Speed limits, signals, road conditions
2. SafetySpec.v - Following distance, stopping distance formulas
3. SignatureSpec.v - Cryptographic signature infrastructure (all inputs must be signed)
4. ComplianceSpec.v - Main compliance predicate requiring inputs_certified AND safety properties

Critical: All sensor data must have TPM signatures, maps must have Ministry signatures,
signals must have infrastructure signatures. Compliance proof is INVALID if any signature fails.

Key design decisions:
• All measurements in mm/ms for integer arithmetic
• Conservative uncertainty handling (position - uncertainty - length/2)
• inputs_certified as prerequisite to any compliance claim
• STL for real-time (<1ms), Coq for completeness (audit)

Generate complete working Coq code with example proof.""",

    "consumer_protection": """Create a Coq specification for e-commerce recommendation compliance that proves:
- User preferences are cryptographically signed (not fabricated)
- Recommended products are in certified catalog
- Products meet user's hard constraints (budget, rating, excluded brands)
- OPTIMALITY: Recommended product maximizes user utility (no manipulation)
- All commercial relationships (affiliate, sponsored) are disclosed
- No hidden influence on rankings

The Consumer Protection Authority publishes:
1. UserPreference.v - Preference weights, constraints, signature validation
2. ProductSpec.v - Product attributes, catalog certification
3. DisclosureSpec.v - Commercial relationship disclosure requirements
4. FairRankingSpec.v - Ranking must match utility order
5. RecommendationComplianceSpec.v - Main compliance predicate

Key design decisions:
• Utility function: compute_utility with weighted factors (price, quality, features, brand, sustainability)
• Optimality: forall other, utility(other) <= utility(recommended)
• Disclosure types: Affiliate, Sponsored, OwnProduct, Partnership, None
• Near-compliance mode with tolerance parameter

Generate complete working Coq code with example proof."""
}

VERIFIERS = ["coqc", "rcoq", "coqide"]


class PCODashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("PCO Framework - Provably Compliant Outcomes")
        self.root.geometry("1200x800")
        
        self.storage_dir = Path("pco_storage")
        self.storage_dir.mkdir(exist_ok=True)
        
        self.blockchain_file = self.storage_dir / "blockchain.json"
        self.load_blockchain()
        
        self.current_proof_file = None
        self.current_proposition = None
        self.verification_passed = False
        
        self.create_widgets()
    
    def load_blockchain(self):
        """Load blockchain records"""
        if self.blockchain_file.exists():
            with open(self.blockchain_file, 'r') as f:
                self.blockchain = json.load(f)
        else:
            self.blockchain = []
    
    def save_blockchain(self):
        """Save blockchain records"""
        with open(self.blockchain_file, 'w') as f:
            json.dump(self.blockchain, f, indent=2)
    
    def create_widgets(self):
        # Title
        title = tk.Label(self.root, text="PCO Framework", font=("Arial", 18, "bold"))
        title.pack(pady=10)
        subtitle = tk.Label(self.root, text="Provably Compliant Outcomes", font=("Arial", 12))
        subtitle.pack()
        
        # Configuration Frame
        config_frame = ttk.LabelFrame(self.root, text="Configuration", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Use Case Selection
        ttk.Label(config_frame, text="Use Case:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.use_case_var = tk.StringVar(value="tax_compliance")
        use_case_combo = ttk.Combobox(config_frame, textvariable=self.use_case_var,
                                       values=list(PCO_PROMPTS.keys()), state="readonly", width=30)
        use_case_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Button(config_frame, text="View Prompt", command=self.view_prompt).grid(row=0, column=2, padx=5)
        
        # Verifier Selection
        ttk.Label(config_frame, text="Verifier:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.verifier_var = tk.StringVar(value="coqc")
        verifier_combo = ttk.Combobox(config_frame, textvariable=self.verifier_var,
                                       values=VERIFIERS, state="readonly", width=30)
        verifier_combo.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # LLM API Key
        ttk.Label(config_frame, text="LLM API Key:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.api_key_var = tk.StringVar(value=os.getenv("OPENAI_API_KEY", ""))
        ttk.Entry(config_frame, textvariable=self.api_key_var, show="*", width=40).grid(row=2, column=1, sticky=tk.EW, padx=5)
        
        config_frame.columnconfigure(1, weight=1)
        
        # Action Buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        self.execute_btn = ttk.Button(button_frame, text="Execute (Generate & Verify)", 
                                       command=self.execute_pipeline, width=25)
        self.execute_btn.pack(side=tk.LEFT, padx=5)
        
        self.record_btn = ttk.Button(button_frame, text="Record to Blockchain", 
                                      command=self.record_to_blockchain, state=tk.DISABLED, width=25)
        self.record_btn.pack(side=tk.LEFT, padx=5)
        
        # Output Display
        output_frame = ttk.LabelFrame(self.root, text="Output", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, height=20)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # Status Bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def view_prompt(self):
        """View the selected prompt"""
        use_case = self.use_case_var.get()
        prompt = PCO_PROMPTS.get(use_case, "")
        
        # Create new window
        window = tk.Toplevel(self.root)
        window.title(f"Prompt: {use_case}")
        window.geometry("800x600")
        
        text = scrolledtext.ScrolledText(window, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(1.0, prompt)
        text.config(state=tk.DISABLED)
    
    def execute_pipeline(self):
        """Execute: LLM generate → Verify → Show result"""
        self.output_text.delete(1.0, tk.END)
        self.verification_passed = False
        self.record_btn.config(state=tk.DISABLED)
        
        use_case = self.use_case_var.get()
        verifier = self.verifier_var.get()
        api_key = self.api_key_var.get()
        
        self.log("=" * 70)
        self.log(f"PCO Pipeline: {use_case}")
        self.log("=" * 70)
        self.log()
        
        # Step 1: Generate Coq code via LLM
        self.status_var.set("Generating Coq code from LLM...")
        self.log("Step 1: Generating Coq proof from LLM...")
        
        if not api_key:
            self.log("❌ Error: No API key provided")
            self.log("Set OPENAI_API_KEY environment variable or enter manually")
            self.status_var.set("Error: No API key")
            return
        
        try:
            coq_code, proposition = self.call_llm(PCO_PROMPTS[use_case], api_key)
            self.current_proposition = proposition
            
            self.log(f"✓ Generated Coq code ({len(coq_code)} chars)")
            self.log(f"✓ Proposition: {proposition}")
            self.log()
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{use_case}_{timestamp}.v"
            filepath = self.storage_dir / filename
            
            with open(filepath, 'w') as f:
                f.write(coq_code)
            
            self.current_proof_file = filepath
            self.log(f"✓ Saved to: {filepath}")
            self.log()
            
        except Exception as e:
            self.log(f"❌ Error generating code: {e}")
            self.status_var.set(f"Error: {e}")
            return
        
        # Step 2: Verify with Coq
        self.status_var.set(f"Verifying with {verifier}...")
        self.log(f"Step 2: Verifying with {verifier}...")
        
        try:
            result = subprocess.run(
                [verifier, str(filepath)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            self.log(f"Verifier output:")
            self.log(result.stdout)
            
            if result.stderr:
                self.log(f"Errors:")
                self.log(result.stderr)
            
            if result.returncode == 0:
                self.log()
                self.log("=" * 70)
                self.log("✅ VERIFICATION: PASS")
                self.log("=" * 70)
                self.verification_passed = True
                self.record_btn.config(state=tk.NORMAL)
                self.status_var.set("PASS - Ready to record")
                messagebox.showinfo("Verification Result", "PASS ✓\nProof is valid!")
            else:
                self.log()
                self.log("=" * 70)
                self.log("❌ VERIFICATION: FAIL")
                self.log("=" * 70)
                self.status_var.set("FAIL - Proof invalid")
                messagebox.showerror("Verification Result", "FAIL ✗\nProof has errors")
        
        except subprocess.TimeoutExpired:
            self.log("❌ Verification timeout")
            self.status_var.set("Error: Timeout")
        except FileNotFoundError:
            self.log(f"❌ Verifier '{verifier}' not found")
            self.log("Install Coq: brew install coq")
            self.status_var.set(f"Error: {verifier} not found")
        except Exception as e:
            self.log(f"❌ Error: {e}")
            self.status_var.set(f"Error: {e}")
    
    def call_llm(self, prompt, api_key):
        """
        Call LLM API to generate Coq code.
        Returns: (coq_code, proposition_name)
        """
        try:
            import openai
            openai.api_key = api_key
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a Coq proof assistant. Generate complete, compilable Coq code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            full_response = response.choices[0].message.content
            
            # Extract Coq code (look for code blocks)
            if "```coq" in full_response:
                coq_code = full_response.split("```coq")[1].split("```")[0].strip()
            elif "```" in full_response:
                coq_code = full_response.split("```")[1].split("```")[0].strip()
            else:
                coq_code = full_response
            
            # Extract proposition name (look for Theorem/Definition)
            import re
            match = re.search(r'(Theorem|Definition|Lemma)\s+(\w+)', coq_code)
            proposition = match.group(2) if match else "unknown_proposition"
            
            return coq_code, proposition
        
        except ImportError:
            raise Exception("openai package not installed. Run: pip install openai")
        except Exception as e:
            raise Exception(f"LLM API error: {e}")
    
    def record_to_blockchain(self):
        """Record proof hash to blockchain"""
        if not self.verification_passed or not self.current_proof_file:
            messagebox.showerror("Error", "No verified proof to record")
            return
        
        self.log()
        self.log("=" * 70)
        self.log("Step 3: Recording to Blockchain")
        self.log("=" * 70)
        self.log()
        
        try:
            # Read proof content
            with open(self.current_proof_file, 'r') as f:
                proof_content = f.read()
            
            # Compute hash
            combined = f"{proof_content}|||{self.current_proposition}"
            proof_hash = hashlib.sha256(combined.encode()).hexdigest()
            
            # Create blockchain record
            record = {
                "timestamp": datetime.now().isoformat(),
                "use_case": self.use_case_var.get(),
                "proposition": self.current_proposition,
                "verifier": self.verifier_var.get(),
                "hash": proof_hash,
                "proof_file": str(self.current_proof_file),
                "verification_status": "PASS"
            }
            
            self.blockchain.append(record)
            self.save_blockchain()
            
            self.log(f"✓ Hash: {proof_hash}")
            self.log(f"✓ Timestamp: {record['timestamp']}")
            self.log(f"✓ Proof file: {self.current_proof_file}")
            self.log()
            self.log("✅ Successfully recorded to blockchain!")
            self.log()
            
            self.status_var.set("Recorded to blockchain")
            messagebox.showinfo("Success", f"Proof recorded to blockchain!\n\nHash: {proof_hash[:16]}...")
        
        except Exception as e:
            self.log(f"❌ Error recording: {e}")
            messagebox.showerror("Error", f"Failed to record: {e}")
    
    def log(self, message=""):
        """Log message to output"""
        self.output_text.insert(tk.END, str(message) + "\n")
        self.output_text.see(tk.END)
        self.root.update()


def main():
    root = tk.Tk()
    app = PCODashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
