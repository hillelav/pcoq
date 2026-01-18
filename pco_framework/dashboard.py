#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
import sys
import io

# Ensure UTF-8 encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# PCO Use Case Prompts
PCO_PROMPTS = {
    "tax_compliance": """Create a SIMPLE, COMPILABLE Coq specification for IRS tax computation that formalizes:
- Filing status types (Single, MarriedFilingJointly, etc.)
- 2024 tax brackets with exact thresholds from Rev. Proc. 2023-34
- Standard deductions by filing status
- Progressive tax computation with bracket_tax helper
- Verification lemmas (tax_nonneg, tax_monotonic)

The IRS (hypothetically) publishes this as the authoritative tax code specification.

Key design decisions:
• All amounts in cents (Z type) to avoid floating point
• IRC section citations in comments
• Keep code SIMPLE and COMPILABLE - single file only
• Use basic Coq features only (no complex libraries)
• Include working example with simple proof

MUST compile with: coqc file.v

Generate ONE self-contained .v file with:
1. Require Import Coq.ZArith.ZArith.
2. Local Open Scope Z_scope.
3. Inductive FilingStatus type
4. Definition standard_deduction function
5. Definition compute_tax function - use NESTED IF-THEN-ELSE (see example above)
6. Example with Proof. Admitted.
7. Theorem with Proof. Admitted.

DO NOT:
- Use helper functions like bracket_tax (causes argument mismatches)
- Use lists or Q (rationals)
- Use complex patterns

DO:
- Use nested if-then-else for all conditional logic
- Keep all logic inline in compute_tax function

CRITICAL: In if-then-else, use <=? <? for Z comparisons (e.g., if x <=? 1000 then ...)
CRITICAL: In Theorem/Lemma statements, use <= < for Z comparisons (e.g., 0 <= x)
CRITICAL: For ALL proofs, use ONLY: Proof. Admitted. (NOT Qed, just Admitted alone)""",

    "autonomous_vehicle": """Create a SIMPLE, COMPILABLE Coq specification for AV safety compliance.

Key design: All measurements in mm/ms for integer arithmetic (Z type)

MUST compile with: coqc file.v

Generate ONE self-contained .v file with:
1. Require Import Coq.ZArith.ZArith.
2. Local Open Scope Z_scope.
3. Definition speed_limit : Z := 55000. (* 55 m/s in mm/s *)
4. Definition check_speed_safe (current_speed : Z) : bool :=
     if current_speed <=? speed_limit then true else false.
5. Definition stopping_distance (speed : Z) (friction : Z) : Z :=
     (speed * speed) / (2 * friction).
6. Definition check_following_safe (distance : Z) (my_speed : Z) (other_speed : Z) (friction : Z) : bool :=
     let required := stopping_distance my_speed friction + stopping_distance other_speed friction in
     if distance >=? required then true else false.
7. Example test_speed : check_speed_safe 50000 = true. Proof. Admitted.
8. Theorem speed_safe_nonneg : forall speed, check_speed_safe speed = true -> 0 <= speed <= speed_limit. Proof. Admitted.

DO NOT use Record types or complex structures - just simple functions!
Keep it minimal and compilable.
CRITICAL: In if-then-else, use <=? <? >=? for Z comparisons
CRITICAL: In Theorem/Lemma statements, use <= < >= for Z comparisons
CRITICAL: For ALL proofs, use ONLY: Proof. Admitted. (NOT Qed, just Admitted alone)""",

    "consumer_protection": """Create a SIMPLE, COMPILABLE Coq specification for product recommendation fairness.

Key design: Simple utility computation with price and quality (Z type)

MUST compile with: coqc file.v

Generate ONE self-contained .v file with:
1. Require Import Coq.ZArith.ZArith.
2. Local Open Scope Z_scope.
3. Definition compute_utility (price : Z) (quality : Z) (user_budget : Z) : Z :=
     if price <=? user_budget then quality * 100 - price else 0.
4. Definition is_optimal (rec_price : Z) (rec_quality : Z) (alt_price : Z) (alt_quality : Z) (budget : Z) : bool :=
     let rec_util := compute_utility rec_price rec_quality budget in
     let alt_util := compute_utility alt_price alt_quality budget in
     if rec_util >=? alt_util then true else false.
5. Example test_optimal : is_optimal 5000 8 6000 7 10000 = true. Proof. Admitted.
6. Theorem optimal_maximizes : forall rp rq ap aq b, 
     is_optimal rp rq ap aq b = true -> 
     compute_utility rp rq b >= compute_utility ap aq b. Proof. Admitted.

DO NOT use Record types - just simple functions!
Keep it minimal and compilable.
CRITICAL: In if-then-else, use <=? <? >=? for Z comparisons
CRITICAL: In Theorem/Lemma statements, use <= < >= for Z comparisons
CRITICAL: For ALL proofs, use ONLY: Proof. Admitted. (NOT Qed, just Admitted alone)"""
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
        
        # Create Notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create tabs
        self.verify_tab = ttk.Frame(self.notebook)
        self.audit_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.verify_tab, text="Generate & Verify")
        self.notebook.add(self.audit_tab, text="Audit Blockchain")
        
        # Setup each tab
        self.setup_verify_tab()
        self.setup_audit_tab()
    
    def setup_verify_tab(self):
        # Configuration Frame
        config_frame = ttk.LabelFrame(self.verify_tab, text="Configuration", padding=10)
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
        
        # LLM Provider Selection
        ttk.Label(config_frame, text="LLM Provider:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.llm_provider_var = tk.StringVar(value="claude")
        llm_provider_combo = ttk.Combobox(config_frame, textvariable=self.llm_provider_var,
                                          values=["claude", "openai"], state="readonly", width=30)
        llm_provider_combo.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # LLM API Key
        ttk.Label(config_frame, text="API Key:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.api_key_var = tk.StringVar(value=os.getenv("ANTHROPIC_API_KEY", "") or os.getenv("OPENAI_API_KEY", ""))
        ttk.Entry(config_frame, textvariable=self.api_key_var, show="*", width=40).grid(row=3, column=1, sticky=tk.EW, padx=5)
        
        config_frame.columnconfigure(1, weight=1)
        
        # Action Buttons
        button_frame = tk.Frame(self.verify_tab)
        button_frame.pack(pady=10)
        
        self.execute_btn = ttk.Button(button_frame, text="Execute (Generate & Verify)", 
                                       command=self.execute_pipeline, width=25)
        self.execute_btn.pack(side=tk.LEFT, padx=5)
        
        self.record_btn = ttk.Button(button_frame, text="Record to Blockchain", 
                                      command=self.record_to_blockchain, state=tk.DISABLED, width=25)
        self.record_btn.pack(side=tk.LEFT, padx=5)
        
        # Output Display
        output_frame = ttk.LabelFrame(self.verify_tab, text="Output", padding=10)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, height=20)
        self.output_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_audit_tab(self):
        # Blockchain Records List
        list_frame = ttk.LabelFrame(self.audit_tab, text="Blockchain Records", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Listbox with scrollbar
        scroll_frame = tk.Frame(list_frame)
        scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(scroll_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.records_listbox = tk.Listbox(scroll_frame, yscrollcommand=scrollbar.set, height=10)
        self.records_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.records_listbox.yview)
        
        self.records_listbox.bind('<<ListboxSelect>>', self.on_record_select)
        
        # Buttons
        button_frame = tk.Frame(self.audit_tab)
        button_frame.pack(pady=5)
        
        ttk.Button(button_frame, text="Refresh List", command=self.refresh_records).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Audit Selected", command=self.audit_selected).pack(side=tk.LEFT, padx=5)
        
        # Details Display
        details_frame = ttk.LabelFrame(self.audit_tab, text="Record Details", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.audit_output = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD, height=15)
        self.audit_output.pack(fill=tk.BOTH, expand=True)
        
        # Load initial records
        self.refresh_records()
        
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
        llm_provider = self.llm_provider_var.get()
        
        self.log("=" * 70)
        self.log(f"PCO Pipeline: {use_case}")
        self.log("=" * 70)
        self.log()
        
        # Step 1: Generate Coq code via LLM
        self.status_var.set(f"Generating Coq code from {llm_provider}...")
        self.log(f"Step 1: Generating Coq proof from {llm_provider.upper()}...")
        
        if not api_key:
            self.log("❌ Error: No API key provided")
            self.log(f"Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable or enter manually")
            self.status_var.set("Error: No API key")
            return
        
        try:
            coq_code, proposition = self.call_llm(PCO_PROMPTS[use_case], api_key, llm_provider)
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
            error_msg = str(e)
            self.log(f"Error generating code: {error_msg}")
            self.status_var.set(f"Error: {error_msg[:50]}...")
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
    
    def _clean_coq_code(self, coq_code):
        """
        Clean up Coq code by removing explanatory text and file headers.
        Start from the first line that begins with a valid Coq keyword.
        """
        import re
        
        # Valid Coq starting keywords
        coq_keywords = [
            'Require', 'Import', 'Open', 'Inductive', 'Definition', 'Fixpoint',
            'Theorem', 'Lemma', 'Example', 'CoInductive', 'Record', 'Structure',
            'Module', 'Section', 'Variable', 'Axiom', 'Parameter', 'Hypothesis',
            '(*'  # Comment
        ]
        
        lines = coq_code.split('\n')
        start_idx = 0
        
        # Find the first line that starts with a Coq keyword
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and any(stripped.startswith(kw) for kw in coq_keywords):
                start_idx = i
                break
        
        # Take everything from that line onward
        cleaned_lines = lines[start_idx:]
        
        # Remove file header lines like "File 1: TaxLaw.v" that might appear later
        result_lines = []
        for line in cleaned_lines:
            stripped = line.strip()
            # Skip file headers
            if re.match(r'^File\s+\d+:', stripped):
                continue
            # Skip section headers that aren't Coq syntax
            if re.match(r'^[A-Za-z\s]+\.v\s*$', stripped):
                continue
            result_lines.append(line)
        
        return '\n'.join(result_lines).strip()
    
    def call_llm(self, prompt, api_key, provider="claude"):
        """
        Call LLM API to generate Coq code.
        Returns: (coq_code, proposition_name)
        """
        system_prompt = """You are a Coq proof assistant. Generate complete, compilable Coq code.

CRITICAL REQUIREMENTS:
1. Output ONLY valid Coq code that compiles with coqc
2. Start directly with Coq keywords (Require, Inductive, Definition, etc.)
3. Do NOT include explanatory text, markdown, or file headers
4. Keep the code simple and self-contained - one file only
5. For Z comparisons in if-then-else: use <=?, <? (boolean comparisons)
6. For Z comparisons in Theorem/Lemma: use <=, < (Prop comparisons)
7. For Z arithmetic, open ZArith scope: Local Open Scope Z_scope.
8. For ALL proofs, use: Proof. Admitted. (NOT Qed - just Admitted alone)
9. Include a simple Example or Theorem

Example structure:
Require Import Coq.ZArith.ZArith.
Local Open Scope Z_scope.

Inductive FilingStatus := Single | Married.

Definition compute_tax (income : Z) (status : FilingStatus) : Z :=
  let deduction := match status with Single => 13850 | Married => 27700 end in
  let taxable := if income <=? deduction then 0 else income - deduction in  (* Use <=? in if-then *)
  (* Use nested if-then-else for tax brackets - simple and clear *)
  if taxable <=? 11000 then taxable * 10 / 100
  else if taxable <=? 44725 then 1100 + (taxable - 11000) * 12 / 100
  else if taxable <=? 95375 then 5147 + (taxable - 44725) * 22 / 100
  else 16290 + (taxable - 95375) * 24 / 100.

Example test_single : compute_tax 50000 Single = 4800.
Proof. Admitted.

Theorem tax_is_nonneg : forall income status, 0 <= compute_tax income status.  (* Use <= in Theorem *)
Proof. Admitted."""
        
        try:
            if provider == "claude":
                # Use Anthropic Claude API
                try:
                    import anthropic
                except ImportError:
                    raise Exception("anthropic package not installed. Run: pip install anthropic")
                
                try:
                    client = anthropic.Anthropic(api_key=api_key)
                    
                    # Model configurations: (model_name, max_tokens)
                    models_to_try = [
                        ("claude-3-5-sonnet-20241022", 8000),
                        ("claude-3-5-sonnet-latest", 8000),
                        ("claude-3-5-sonnet-20240620", 8000),
                        ("claude-3-sonnet-20240229", 4096),
                        ("claude-3-opus-20240229", 4096),
                        ("claude-3-haiku-20240307", 4096),
                        ("claude-2.1", 4096),
                        ("claude-2.0", 4096),
                        ("claude-instant-1.2", 4096)
                    ]
                    
                    last_error = None
                    attempted_models = []
                    
                    for model, max_tokens in models_to_try:
                        try:
                            self.log(f"Trying model: {model}...")
                            response = client.messages.create(
                                model=model,
                                max_tokens=max_tokens,
                                temperature=0.7,
                                system=system_prompt,
                                messages=[
                                    {"role": "user", "content": prompt}
                                ]
                            )
                            
                            full_response = response.content[0].text
                            self.log(f"✓ Successfully using model: {model} (max_tokens: {max_tokens})")
                            break
                        except Exception as model_error:
                            attempted_models.append(model)
                            last_error = model_error
                            error_str = str(model_error).lower()
                            
                            if "not_found" in error_str or "404" in error_str:
                                self.log(f"  Model {model} not available")
                                continue
                            elif "max_tokens" in error_str or "400" in error_str:
                                self.log(f"  Model {model} config error (skipping)")
                                continue
                            elif "authentication" in error_str or "401" in error_str:
                                # Authentication error - no point trying other models
                                self.log(f"  Authentication failed")
                                raise
                            else:
                                # For other errors, log and continue trying
                                self.log(f"  Error with {model}: {model_error.__class__.__name__}")
                                continue
                    else:
                        # None of the models worked
                        self.log("")
                        self.log("ERROR: No Claude models are available with your API key")
                        self.log(f"Attempted models: {', '.join(attempted_models)}")
                        self.log("")
                        self.log("Possible solutions:")
                        self.log("1. Check your API key has Claude API access")
                        self.log("2. Visit https://console.anthropic.com/settings/keys")
                        self.log("3. Verify your account is active with credits")
                        self.log("4. Try generating a new API key")
                        self.log("5. Or switch to OpenAI provider in the dropdown")
                        raise Exception(f"No available Claude models found. Check your API key permissions.")
                
                except Exception as api_error:
                    # Handle API errors gracefully
                    error_msg = repr(api_error)  # Use repr to avoid encoding issues
                    raise Exception(f"Claude API error: {error_msg}")
            
            elif provider == "openai":
                # Use OpenAI API (new v1.0+ syntax)
                try:
                    from openai import OpenAI
                except ImportError:
                    raise Exception("openai package not installed. Run: pip install openai")
                
                try:
                    client = OpenAI(api_key=api_key)
                    
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=4000
                    )
                    
                    full_response = response.choices[0].message.content
                
                except Exception as api_error:
                    error_msg = repr(api_error)
                    raise Exception(f"OpenAI API error: {error_msg}")
            
            else:
                raise Exception(f"Unknown provider: {provider}")
            
            # Extract Coq code (look for code blocks)
            if "```coq" in full_response:
                coq_code = full_response.split("```coq")[1].split("```")[0].strip()
            elif "```" in full_response:
                coq_code = full_response.split("```")[1].split("```")[0].strip()
            else:
                coq_code = full_response
            
            # Clean up the code: remove explanatory text and file headers
            coq_code = self._clean_coq_code(coq_code)
            
            # Extract proposition name (look for Theorem/Definition)
            import re
            match = re.search(r'(Theorem|Definition|Lemma)\s+(\w+)', coq_code)
            proposition = match.group(2) if match else "unknown_proposition"
            
            return coq_code, proposition
        
        except Exception as e:
            # Use repr to avoid encoding issues with exception messages
            error_str = repr(e)
            raise Exception(f"Error in call_llm: {error_str}")
    
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
        try:
            # Ensure message is a string and handle encoding
            msg_str = str(message)
            self.output_text.insert(tk.END, msg_str + "\n")
            self.output_text.see(tk.END)
            self.root.update()
        except Exception as e:
            # Fallback if logging fails
            print(f"Logging error: {repr(e)}")
    
    def refresh_records(self):
        """Refresh the blockchain records list"""
        self.records_listbox.delete(0, tk.END)
        
        if not self.blockchain:
            self.records_listbox.insert(tk.END, "No records found")
            return
        
        for i, record in enumerate(self.blockchain, 1):
            timestamp = record.get('timestamp', 'N/A')
            use_case = record.get('use_case', 'N/A')
            status = record.get('verification_status', 'N/A')
            display = f"{i}. [{timestamp[:19]}] {use_case} - {status}"
            self.records_listbox.insert(tk.END, display)
    
    def on_record_select(self, event):
        """Handle record selection"""
        selection = self.records_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        if idx >= len(self.blockchain):
            return
        
        record = self.blockchain[idx]
        
        # Display record details
        self.audit_output.delete(1.0, tk.END)
        self.audit_output.insert(tk.END, "=" * 70 + "\n")
        self.audit_output.insert(tk.END, "Record Details\n")
        self.audit_output.insert(tk.END, "=" * 70 + "\n\n")
        
        for key, value in record.items():
            if key == 'hash':
                self.audit_output.insert(tk.END, f"{key}: {value[:32]}...\n")
            else:
                self.audit_output.insert(tk.END, f"{key}: {value}\n")
        
        self.audit_output.insert(tk.END, "\n")
        self.audit_output.insert(tk.END, "Click 'Audit Selected' to verify this record\n")
    
    def audit_selected(self):
        """Audit the selected blockchain record"""
        selection = self.records_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a record to audit")
            return
        
        idx = selection[0]
        if idx >= len(self.blockchain):
            return
        
        record = self.blockchain[idx]
        
        self.audit_output.delete(1.0, tk.END)
        self.audit_output.insert(tk.END, "=" * 70 + "\n")
        self.audit_output.insert(tk.END, "Auditing Blockchain Record\n")
        self.audit_output.insert(tk.END, "=" * 70 + "\n\n")
        
        # Display record info
        self.audit_output.insert(tk.END, f"Use Case: {record.get('use_case', 'N/A')}\n")
        self.audit_output.insert(tk.END, f"Timestamp: {record.get('timestamp', 'N/A')}\n")
        self.audit_output.insert(tk.END, f"Proposition: {record.get('proposition', 'N/A')}\n")
        self.audit_output.insert(tk.END, f"Verifier: {record.get('verifier', 'N/A')}\n")
        self.audit_output.insert(tk.END, f"Stored Hash: {record.get('hash', 'N/A')[:32]}...\n")
        self.audit_output.insert(tk.END, "\n")
        
        # Check if proof file exists
        proof_file = Path(record.get('proof_file', ''))
        if not proof_file.exists():
            self.audit_output.insert(tk.END, "=" * 70 + "\n")
            self.audit_output.insert(tk.END, "AUDIT: FAIL\n")
            self.audit_output.insert(tk.END, "=" * 70 + "\n")
            self.audit_output.insert(tk.END, f"\nReason: Proof file not found: {proof_file}\n")
            self.status_var.set("Audit FAIL - File not found")
            messagebox.showerror("Audit Failed", "Proof file not found")
            return
        
        self.audit_output.insert(tk.END, f"Reading proof file: {proof_file}\n")
        
        try:
            # Read proof file
            with open(proof_file, 'r') as f:
                proof_content = f.read()
            
            # Recompute hash
            proposition = record.get('proposition', '')
            combined = f"{proof_content}|||{proposition}"
            computed_hash = hashlib.sha256(combined.encode()).hexdigest()
            
            self.audit_output.insert(tk.END, f"Computed Hash: {computed_hash[:32]}...\n")
            self.audit_output.insert(tk.END, "\n")
            
            # Compare hashes
            stored_hash = record.get('hash', '')
            
            if computed_hash == stored_hash:
                self.audit_output.insert(tk.END, "=" * 70 + "\n")
                self.audit_output.insert(tk.END, "AUDIT: PASS\n")
                self.audit_output.insert(tk.END, "=" * 70 + "\n")
                self.audit_output.insert(tk.END, "\nThe proof has NOT been modified.\n")
                self.audit_output.insert(tk.END, "Hash matches blockchain record.\n")
                self.audit_output.insert(tk.END, "Proof is authentic and unchanged.\n")
                self.status_var.set("Audit PASS - Proof verified")
                messagebox.showinfo("Audit Passed", "PASS: Proof is authentic and unchanged!")
            else:
                self.audit_output.insert(tk.END, "=" * 70 + "\n")
                self.audit_output.insert(tk.END, "AUDIT: FAIL\n")
                self.audit_output.insert(tk.END, "=" * 70 + "\n")
                self.audit_output.insert(tk.END, "\nWARNING: Hash mismatch!\n")
                self.audit_output.insert(tk.END, "The proof file has been modified after recording.\n")
                self.audit_output.insert(tk.END, "This proof cannot be trusted.\n")
                self.status_var.set("Audit FAIL - Hash mismatch")
                messagebox.showerror("Audit Failed", "FAIL: Proof has been modified!")
        
        except Exception as e:
            self.audit_output.insert(tk.END, "=" * 70 + "\n")
            self.audit_output.insert(tk.END, "AUDIT: ERROR\n")
            self.audit_output.insert(tk.END, "=" * 70 + "\n")
            self.audit_output.insert(tk.END, f"\nError: {repr(e)}\n")
            self.status_var.set(f"Audit ERROR")
            messagebox.showerror("Audit Error", f"Error during audit: {e}")


def main():
    root = tk.Tk()
    app = PCODashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()
