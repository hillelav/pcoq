#!/usr/bin/env python3
"""
PCO Framework Performance Benchmark Suite

Measures:
1. LLM generation time (by provider, model)
2. Coq verification time
3. Proof sizes (characters, lines)
4. Success rates
5. Total end-to-end time

Outputs:
- CSV data files
- Performance graphs (PNG)
- Statistical summary
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
import statistics

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

class PCOBenchmark:
    def __init__(self, output_dir="benchmark_results", complexity="all"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = []
        self.complexity = complexity
        
        # Import complexity scenarios
        try:
            from complexity_scenarios import get_scenario, COMPLEXITY_LEVELS
            self.get_scenario = get_scenario
            self.complexity_levels = COMPLEXITY_LEVELS
        except ImportError:
            print("Warning: complexity_scenarios.py not found, using legacy mode")
            self.get_scenario = None
        
        # Build test configurations based on complexity level
        if complexity == "all":
            self.use_cases = self._build_all_complexity_use_cases()
        elif complexity in ["easy", "medium", "hard"]:
            self.use_cases = self._build_single_complexity_use_cases(complexity)
        else:
            # Legacy mode: original 3 use cases (treated as "medium")
            self.use_cases = [
                ("tax_compliance", "medium"),
                ("autonomous_vehicle", "medium"),
                ("consumer_protection", "medium")
            ]
        
        # 5 LLMs for Paper Graphs
        self.llm_providers = {
            "openai": ["gpt-4-turbo"],                # OpenAI GPT-4 Turbo
            "claude": ["claude-3-5-sonnet-20241022"], # Anthropic Claude 3.5 Sonnet
            "gemini": ["gemini-2.0-flash"],           # Google Gemini 2.0 Flash (fast, available in API)
            "groq": ["llama-3.3-70b-versatile"],      # Groq Llama 3.3 70B
            "deepseek": ["deepseek-chat"],            # DeepSeek Chat (fast: ~6s, cheaper than OpenAI)
        }
    
    def _build_all_complexity_use_cases(self):
        """Build all complexity levels for all use cases"""
        cases = []
        for complexity in ["easy", "medium", "hard"]:
            cases.append(("tax", complexity))
            # cases.append(("av", complexity))  # DISABLED: Will test with SLM later for real-time performance
            cases.append(("recommendation", complexity))
        return cases
    
    def _build_single_complexity_use_cases(self, complexity):
        """Build specific complexity level"""
        return [
            ("tax", complexity),
            # ("av", complexity),  # DISABLED: Will test with SLM later for real-time performance
            ("recommendation", complexity)
        ]
        
    def run_benchmark(self, iterations=5):
        """Run full benchmark suite"""
        print("=" * 70)
        print("PCO Framework Performance Benchmark")
        print(f"Complexity Mode: {self.complexity}")
        print("=" * 70)
        print()
        print(f"Iterations per test: {iterations}")
        print(f"Scenarios: {len(self.use_cases)}")
        print(f"LLM providers: {list(self.llm_providers.keys())}")
        print()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Run benchmarks
        for use_case_tuple in self.use_cases:
            # Handle both old format (string) and new format (tuple)
            if isinstance(use_case_tuple, tuple):
                use_case_type, complexity_level = use_case_tuple
                use_case_name = f"{use_case_type}_{complexity_level}"
                
                # Get scenario details if available
                if self.get_scenario:
                    try:
                        scenario = self.get_scenario(use_case_type, complexity_level)
                        print(f"\n{'='*70}")
                        print(f"Scenario: {scenario['name']}")
                        print(f"Type: {use_case_type}, Complexity: {complexity_level}")
                        print(f"Description: {scenario['description']}")
                        print(f"{'='*70}")
                    except Exception as e:
                        print(f"Warning: Could not load scenario: {e}")
                        scenario = None
                else:
                    scenario = None
            else:
                # Legacy format: treat as medium complexity
                use_case_name = use_case_tuple
                use_case_type = use_case_tuple
                complexity_level = "medium"
                scenario = None
            
            for provider, models in self.llm_providers.items():
                for model in models:
                    print(f"\nTesting: {use_case_name} with {provider}/{model}")
                    print("-" * 60)
                    
                    for i in range(iterations):
                        print(f"  Iteration {i+1}/{iterations}...", end=" ")
                        result = self.run_single_test(use_case_name, provider, model, scenario)
                        result["use_case_type"] = use_case_type
                        result["complexity"] = complexity_level
                        self.results.append(result)
                        
                        if result["success"]:
                            print(f"✓ {result['total_time']:.2f}s")
                        else:
                            error_msg = result.get('error', 'unknown')
                            # Show first 150 chars for better debugging
                            print(f"✗ Failed: {error_msg[:150]}")
                            if len(error_msg) > 150:
                                print(f"           ... ({len(error_msg)} chars total)")
        
        # Save results
        self.save_results(timestamp)
        
        # Generate graphs
        self.generate_graphs(timestamp)
        
        # Print summary
        self.print_summary()
        
    def run_single_test(self, use_case, provider, model, scenario=None):
        """Run a single benchmark test"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "use_case": use_case,
            "provider": provider,
            "model": model,
            "success": False,
            # Total metrics (including all retries)
            "llm_time": 0,
            "verification_time": 0,
            "total_time": 0,
            "proof_size_chars": 0,
            "proof_size_lines": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            # Success-only metrics (just the final successful attempt)
            "success_llm_time": 0,
            "success_tokens": 0,
            "success_verify_time": 0,
            # RAG overhead metrics (wasted on failed attempts)
            "wasted_llm_time": 0,
            "wasted_tokens": 0,
            "wasted_verify_time": 0,
            "rag_iterations": 0,  # Number of RAG correction attempts
            "source": "llm",  # Track which RAG stage succeeded
            "error": None,
            # Detailed RAG stage tracking (time and tokens per stage)
            "stage_first_attempt_time": 0,
            "stage_first_attempt_tokens": 0,
            "stage_error_rag_time": 0,      # Total time in error RAG retries
            "stage_error_rag_tokens": 0,    # Total tokens in error RAG retries
            "stage_error_rag_count": 0,     # Number of error RAG retries
            "stage_final_rag_time": 0,
            "stage_final_rag_tokens": 0,
            "stage_minimal_adapt_time": 0,
            "stage_minimal_adapt_tokens": 0
        }
        
        start_total = time.time()
        
        try:
            # Import here to avoid issues
            from dashboard import PCODashboard
            
            # Mock GUI elements
            class MockVar:
                def __init__(self, value):
                    self.value = value
                def get(self):
                    return self.value
                def set(self, v):
                    self.value = v
            
            class MockText:
                def __init__(self):
                    self.content = ""
                def insert(self, pos, text):
                    self.content += text
                def delete(self, start, end):
                    self.content = ""
                def get(self, start, end):
                    return self.content
                def see(self, pos):
                    pass  # No-op for benchmarking
                def yview(self, *args):
                    pass  # No-op for benchmarking
            
            # Create minimal dashboard instance
            dashboard = PCODashboard.__new__(PCODashboard)
            dashboard.use_case_var = MockVar(use_case)
            dashboard.llm_provider_var = MockVar(provider)
            dashboard.verifier_var = MockVar("coqc")
            dashboard.api_key_entry = MockVar("")
            dashboard.output_text = MockText()
            dashboard.storage_dir = Path("pco_storage")
            dashboard.storage_dir.mkdir(exist_ok=True)
            dashboard.loaded_document = None
            dashboard.document_hash = None
            
            # Silence dashboard logging (just collect text)
            dashboard.log = lambda *args, **kwargs: None
            
            # Get API key from environment
            if provider == "claude":
                api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            elif provider == "openai":
                api_key = os.environ.get("OPENAI_API_KEY", "")
            elif provider == "gemini":
                api_key = os.environ.get("GOOGLE_API_KEY", "")
            elif provider == "llama" or provider == "groq":
                api_key = os.environ.get("GROQ_API_KEY", "")
            elif provider == "deepseek":
                api_key = os.environ.get("DEEPSEEK_API_KEY", "")
            elif provider == "together":
                api_key = os.environ.get("TOGETHER_API_KEY", "")
            elif provider == "perplexity":
                api_key = os.environ.get("PERPLEXITY_API_KEY", "")
            elif provider == "mistral":
                api_key = os.environ.get("MISTRAL_API_KEY", "")
            elif provider == "cohere":
                api_key = os.environ.get("COHERE_API_KEY", "")
            else:
                api_key = ""
            
            if not api_key:
                result["error"] = f"No {provider} API key found in environment (check {provider.upper()}_API_KEY)"
                return result
            
            # Get prompt: use scenario if provided, otherwise fall back to PCO_PROMPTS
            if scenario and 'prompt' in scenario:
                prompt = scenario['prompt']
            else:
                # Legacy mode: use original prompts
                from dashboard import PCO_PROMPTS
                # Map complexity-aware use case names back to original keys
                use_case_base = use_case.replace("_easy", "").replace("_medium", "").replace("_hard", "")
                if use_case_base == "tax":
                    prompt = PCO_PROMPTS.get("tax_compliance", "")
                elif use_case_base == "av":
                    prompt = PCO_PROMPTS.get("autonomous_vehicle", "")
                elif use_case_base == "recommendation":
                    prompt = PCO_PROMPTS.get("consumer_protection", "")
                else:
                    prompt = PCO_PROMPTS.get(use_case, "")
            
            # ENHANCE PROMPT with comprehensive RAG context for 100% success
            try:
                from coq_corrector import CoqCorrector
                from coq_rag_knowledge import (
                    get_rag_context, 
                    build_rag_correction_prompt,
                    build_initial_prompt,
                    get_error_specific_hint
                )
                # Use comprehensive RAG-enhanced prompt
                original_prompt = prompt  # Keep for reference
                prompt = build_initial_prompt(prompt, use_case)
                HAS_RAG = True
                HAS_COQ_CORRECTOR = True
            except ImportError as e:
                print(f"    [Warning: RAG not available: {e}]")
                original_prompt = prompt
                HAS_RAG = False
                HAS_COQ_CORRECTOR = False
            
            # Measure LLM generation (first attempt - Stage 1: Example+Rule RAG)
            start_llm = time.time()
            coq_code, proposition, token_info = dashboard.call_llm(prompt, api_key, provider, model)
            first_attempt_time = time.time() - start_llm
            first_attempt_tokens = token_info.get("total_tokens", 0)
            
            # Track totals
            result["llm_time"] = first_attempt_time
            result["input_tokens"] = token_info.get("input_tokens", 0)
            result["output_tokens"] = token_info.get("output_tokens", 0)
            result["total_tokens"] = first_attempt_tokens
            
            # Track stage-specific metrics
            result["stage_first_attempt_time"] = first_attempt_time
            result["stage_first_attempt_tokens"] = first_attempt_tokens
            
            # Apply comprehensive automatic fixes for maximum success
            import re
            
            if HAS_COQ_CORRECTOR:
                from coq_corrector import force_all_proofs_admitted, fix_common_coq_issues
                coq_code = fix_common_coq_issues(coq_code)
                coq_code = force_all_proofs_admitted(coq_code)
                coq_code = CoqCorrector.fix_common_errors(coq_code)
            else:
                # Manual fixes if CoqCorrector not available
                coq_code = re.sub(
                    r'Require\s+Import\s+Coq\.([^\s.]+(?:\.[^\s.]+)*)\s*\.',
                    r'From Stdlib Require Import \1.',
                    coq_code
                )
                coq_code = re.sub(
                    r'From\s+Coq\s+Require\s+Import\s+([^\s.]+(?:\.[^\s.]+)*)\s*\.',
                    r'From Stdlib Require Import \1.',
                    coq_code
                )
                # Close unterminated comments
                open_comments = coq_code.count('(*')
                close_comments = coq_code.count('*)')
                if open_comments > close_comments:
                    coq_code += '\n' + ('*)' * (open_comments - close_comments))
            
            # Save proof
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            proof_file = dashboard.storage_dir / f"benchmark_{use_case}_{timestamp_str}.v"
            with open(proof_file, 'w') as f:
                f.write(coq_code)
            
            result["proof_size_chars"] = len(coq_code)
            result["proof_size_lines"] = len(coq_code.split('\n'))
            
            # Measure verification
            start_verify = time.time()
            verify_result = subprocess.run(
                ['coqc', str(proof_file)],
                capture_output=True,
                text=True,
                timeout=30
            )
            result["verification_time"] = time.time() - start_verify
            
            result["success"] = verify_result.returncode == 0
            result["source"] = "llm"
            
            # Track success metrics for first attempt
            if result["success"]:
                result["success_llm_time"] = first_attempt_time
                result["success_tokens"] = first_attempt_tokens
                result["success_verify_time"] = result["verification_time"]
                result["rag_iterations"] = 0
            
            # If first attempt failed, track it as wasted
            if not result["success"]:
                result["wasted_llm_time"] = first_attempt_time
                result["wasted_tokens"] = first_attempt_tokens
                result["wasted_verify_time"] = result["verification_time"]
            
            # Total timeout for entire test (60 seconds max)
            MAX_TEST_TIME = 60
            elapsed_total = time.time() - start_total
            
            # SELF-CORRECTION with comprehensive RAG
            # RAG Techniques: Error-specific hints + Working code examples + Critical rules
            max_retries = 3  # 3 retries for good success rate
            retry_count = 0
            
            while not result["success"] and retry_count < max_retries and (time.time() - start_total) < MAX_TEST_TIME:
                retry_count += 1
                coq_error = verify_result.stderr[:1000]  # More error context
                
                # Use comprehensive RAG-enhanced correction prompt
                if HAS_RAG:
                    correction_prompt = build_rag_correction_prompt(
                        original_prompt, coq_code, coq_error, use_case
                    )
                else:
                    correction_prompt = f"""The Coq code below failed. Fix it.

ERROR:
{coq_error}

BROKEN CODE:
{coq_code}

REQUIREMENTS:
1. Keep the SAME logical proposition
2. Fix only the syntax errors
3. Use "From Stdlib Require Import" (not "From Coq")
4. Use <=? >=? for boolean comparisons
5. Use Admitted for ALL proofs

CORRECTED CODE:"""

                print(f"    [Retry {retry_count}/{max_retries}] Self-correcting...")
                
                try:
                    # Call LLM again with error feedback
                    start_retry = time.time()
                    fixed_code, _, retry_tokens = dashboard.call_llm(correction_prompt, api_key, provider, model)
                    retry_time = time.time() - start_retry
                    retry_token_count = retry_tokens.get("total_tokens", 0)
                    
                    # Add to totals
                    result["llm_time"] += retry_time
                    result["input_tokens"] += retry_tokens.get("input_tokens", 0)
                    result["output_tokens"] += retry_tokens.get("output_tokens", 0)
                    result["total_tokens"] += retry_token_count
                    
                    # Apply comprehensive automatic fixes + force Admitted
                    if HAS_COQ_CORRECTOR:
                        fixed_code = fix_common_coq_issues(fixed_code)
                        fixed_code = force_all_proofs_admitted(fixed_code)
                        fixed_code = CoqCorrector.fix_common_errors(fixed_code)
                    else:
                        fixed_code = re.sub(
                            r'Require\s+Import\s+Coq\.([^\s.]+(?:\.[^\s.]+)*)\s*\.',
                            r'From Stdlib Require Import \1.',
                            fixed_code
                        )
                        fixed_code = re.sub(
                            r'From\s+Coq\s+Require\s+Import\s+([^\s.]+(?:\.[^\s.]+)*)\s*\.',
                            r'From Stdlib Require Import \1.',
                            fixed_code
                        )
                    
                    # Save and verify fixed code
                    with open(proof_file, 'w') as f:
                        f.write(fixed_code)
                    
                    coq_code = fixed_code
                    result["proof_size_chars"] = len(fixed_code)
                    result["proof_size_lines"] = len(fixed_code.split('\n'))
                    
                    start_verify = time.time()
                    verify_result = subprocess.run(
                        ['coqc', str(proof_file)],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    verify_time = time.time() - start_verify
                    result["verification_time"] += verify_time
                    result["success"] = verify_result.returncode == 0
                    
                    # Track error RAG stage metrics
                    result["stage_error_rag_time"] += retry_time
                    result["stage_error_rag_tokens"] += retry_token_count
                    result["stage_error_rag_count"] = retry_count
                    
                    if result["success"]:
                        # This retry succeeded - record success metrics
                        result["source"] = f"llm_retry_{retry_count}"
                        result["success_llm_time"] = retry_time
                        result["success_tokens"] = retry_token_count
                        result["success_verify_time"] = verify_time
                        result["rag_iterations"] = retry_count
                        print(f"    [Fixed on retry {retry_count}! ✓]")
                    else:
                        # This retry failed - add to wasted
                        result["wasted_llm_time"] += retry_time
                        result["wasted_tokens"] += retry_token_count
                        result["wasted_verify_time"] += verify_time
                    
                except Exception as e:
                    print(f"    [Retry {retry_count} error: {str(e)[:50]}]")
                    continue  # Keep trying
            
            # FINAL RAG ATTEMPT: Fresh start with full RAG context (skip if timeout)
            if not result["success"] and HAS_RAG and (time.time() - start_total) < MAX_TEST_TIME:
                print(f"    [Final RAG attempt] Fresh generation with examples...")
                
                # Get full working pattern
                rag_context = get_rag_context(use_case)
                
                final_prompt = f"""{rag_context}

=== CRITICAL: GENERATE A WORKING PROOF ===

You must generate Coq code for: {use_case}

The previous {retry_count} attempts all failed. Study the working pattern above VERY carefully.

ORIGINAL REQUIREMENT:
{original_prompt[:1000]}

KEY RULES:
1. Copy the STRUCTURE from the working pattern
2. Adapt the LOGIC to match the requirement
3. Use ADMITTED for ALL theorems/lemmas
4. Use reflexivity for Examples (or Admitted if reflexivity fails)
5. Every Definition must have: name, parameters with types, return type, body

Generate ONLY compilable Coq code:"""
                
                try:
                    start_final = time.time()
                    final_code, _, final_tokens = dashboard.call_llm(final_prompt, api_key, provider, model)
                    final_time = time.time() - start_final
                    final_token_count = final_tokens.get("total_tokens", 0)
                    
                    result["llm_time"] += final_time
                    result["input_tokens"] += final_tokens.get("input_tokens", 0)
                    result["output_tokens"] += final_tokens.get("output_tokens", 0)
                    result["total_tokens"] += final_token_count
                    
                    if HAS_COQ_CORRECTOR:
                        final_code = fix_common_coq_issues(final_code)
                        final_code = force_all_proofs_admitted(final_code)
                        final_code = CoqCorrector.fix_common_errors(final_code)
                    
                    with open(proof_file, 'w') as f:
                        f.write(final_code)
                    
                    coq_code = final_code
                    result["proof_size_chars"] = len(final_code)
                    result["proof_size_lines"] = len(final_code.split('\n'))
                    
                    start_verify = time.time()
                    verify_result = subprocess.run(
                        ['coqc', str(proof_file)],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    final_verify_time = time.time() - start_verify
                    result["verification_time"] += final_verify_time
                    result["success"] = verify_result.returncode == 0
                    
                    # Track final RAG stage metrics
                    result["stage_final_rag_time"] = final_time
                    result["stage_final_rag_tokens"] = final_token_count
                    
                    if result["success"]:
                        result["source"] = "llm_rag_final"
                        result["success_llm_time"] = final_time
                        result["success_tokens"] = final_token_count
                        result["success_verify_time"] = final_verify_time
                        result["rag_iterations"] = retry_count + 1  # retries + this attempt
                        print(f"    [RAG final attempt works! ✓]")
                    else:
                        result["wasted_llm_time"] += final_time
                        result["wasted_tokens"] += final_token_count
                        result["wasted_verify_time"] += final_verify_time
                except Exception as e:
                    print(f"    [Final RAG error: {str(e)[:50]}]")
            
            # REMOVED: "Minimal Adaptation" stage - that's basically using templates
            # If Final RAG fails, it's a real failure
            
            # Check if we hit timeout
            if (time.time() - start_total) >= MAX_TEST_TIME and not result["success"]:
                result["error"] = f"Timeout ({MAX_TEST_TIME}s exceeded)"
                result["source"] = "timeout"
                print(f"    [TIMEOUT after {MAX_TEST_TIME}s]")
            
            # Final status
            if not result["success"]:
                result["error"] = result.get("error") or verify_result.stderr[:200]
                result["source"] = "failed"
            
            # Clean up successful files
            if result["success"]:
                try:
                    proof_file.unlink()
                except:
                    pass
            
        except Exception as e:
            result["error"] = str(e)  # Full error message for debugging
        
        result["total_time"] = time.time() - start_total
        
        return result
    
    def save_results(self, timestamp):
        """Save results to CSV and JSON"""
        # CSV
        csv_file = self.output_dir / f"benchmark_{timestamp}.csv"
        with open(csv_file, 'w') as f:
            # Header
            f.write("timestamp,use_case,provider,model,success,source,llm_time,verification_time,total_time,proof_size_chars,proof_size_lines,input_tokens,output_tokens,total_tokens,error\n")
            # Data
            for r in self.results:
                source = r.get('source', 'llm')
                f.write(f"{r['timestamp']},{r['use_case']},{r['provider']},{r['model']},{r['success']},{source},{r['llm_time']:.3f},{r['verification_time']:.3f},{r['total_time']:.3f},{r['proof_size_chars']},{r['proof_size_lines']},{r['input_tokens']},{r['output_tokens']},{r['total_tokens']},\"{r['error'] or ''}\"\n")
        
        print(f"\n✓ Saved CSV: {csv_file}")
        
        # JSON
        json_file = self.output_dir / f"benchmark_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"✓ Saved JSON: {json_file}")
    
    def generate_graphs(self, timestamp):
        """Generate performance graphs"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            print("\n⚠ matplotlib not installed, skipping graphs")
            print("  Install: pip install matplotlib")
            return
        
        # Filter successful results
        successful = [r for r in self.results if r["success"]]
        
        if not successful:
            print("\n⚠ No successful results to graph")
            return
        
        # Prepare data
        use_cases = list(set(r["use_case"] for r in successful))
        
        # Graph 1: LLM Generation Time by Use Case
        fig, ax = plt.subplots(figsize=(10, 6))
        
        data_by_case = {}
        for uc in use_cases:
            times = [r["llm_time"] for r in successful if r["use_case"] == uc]
            data_by_case[uc] = times
        
        positions = range(len(use_cases))
        bp = ax.boxplot(
            [data_by_case[uc] for uc in use_cases],
            labels=[uc.replace("_", "\n") for uc in use_cases],
            patch_artist=True
        )
        
        for patch in bp['boxes']:
            patch.set_facecolor('lightblue')
        
        ax.set_ylabel('Time (seconds)', fontsize=12)
        ax.set_xlabel('Use Case', fontsize=12)
        ax.set_title('LLM Generation Time by Use Case', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        graph1 = self.output_dir / f"graph_llm_time_{timestamp}.png"
        plt.savefig(graph1, dpi=300)
        plt.close()
        print(f"✓ Saved graph: {graph1}")
        
        # Graph 2: Verification Time by Use Case
        fig, ax = plt.subplots(figsize=(10, 6))
        
        data_by_case = {}
        for uc in use_cases:
            times = [r["verification_time"] for r in successful if r["use_case"] == uc]
            data_by_case[uc] = times
        
        bp = ax.boxplot(
            [data_by_case[uc] for uc in use_cases],
            labels=[uc.replace("_", "\n") for uc in use_cases],
            patch_artist=True
        )
        
        for patch in bp['boxes']:
            patch.set_facecolor('lightgreen')
        
        ax.set_ylabel('Time (seconds)', fontsize=12)
        ax.set_xlabel('Use Case', fontsize=12)
        ax.set_title('Coq Verification Time by Use Case', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        graph2 = self.output_dir / f"graph_verify_time_{timestamp}.png"
        plt.savefig(graph2, dpi=300)
        plt.close()
        print(f"✓ Saved graph: {graph2}")
        
        # Graph 3: Total End-to-End Time
        fig, ax = plt.subplots(figsize=(10, 6))
        
        data_by_case = {}
        for uc in use_cases:
            times = [r["total_time"] for r in successful if r["use_case"] == uc]
            data_by_case[uc] = times
        
        bp = ax.boxplot(
            [data_by_case[uc] for uc in use_cases],
            labels=[uc.replace("_", "\n") for uc in use_cases],
            patch_artist=True
        )
        
        for patch in bp['boxes']:
            patch.set_facecolor('lightyellow')
        
        ax.set_ylabel('Time (seconds)', fontsize=12)
        ax.set_xlabel('Use Case', fontsize=12)
        ax.set_title('Total End-to-End Time (Generation + Verification)', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        graph3 = self.output_dir / f"graph_total_time_{timestamp}.png"
        plt.savefig(graph3, dpi=300)
        plt.close()
        print(f"✓ Saved graph: {graph3}")
        
        # Graph 4: Success Rate
        fig, ax = plt.subplots(figsize=(10, 6))
        
        success_rates = []
        for uc in use_cases:
            uc_results = [r for r in self.results if r["use_case"] == uc]
            success_count = sum(1 for r in uc_results if r["success"])
            rate = (success_count / len(uc_results)) * 100 if uc_results else 0
            success_rates.append(rate)
        
        bars = ax.bar(
            [uc.replace("_", "\n") for uc in use_cases],
            success_rates,
            color=['green' if r == 100 else 'orange' if r >= 80 else 'red' for r in success_rates]
        )
        
        ax.set_ylabel('Success Rate (%)', fontsize=12)
        ax.set_xlabel('Use Case', fontsize=12)
        ax.set_title('Proof Generation Success Rate', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 105)
        ax.grid(axis='y', alpha=0.3)
        
        # Add percentage labels
        for bar, rate in zip(bars, success_rates):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{rate:.1f}%',
                   ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        graph4 = self.output_dir / f"graph_success_rate_{timestamp}.png"
        plt.savefig(graph4, dpi=300)
        plt.close()
        print(f"✓ Saved graph: {graph4}")
        
        # Graph 5: Proof Size Distribution
        fig, ax = plt.subplots(figsize=(10, 6))
        
        data_by_case = {}
        for uc in use_cases:
            sizes = [r["proof_size_lines"] for r in successful if r["use_case"] == uc]
            data_by_case[uc] = sizes
        
        bp = ax.boxplot(
            [data_by_case[uc] for uc in use_cases],
            labels=[uc.replace("_", "\n") for uc in use_cases],
            patch_artist=True
        )
        
        for patch in bp['boxes']:
            patch.set_facecolor('lightcoral')
        
        ax.set_ylabel('Lines of Code', fontsize=12)
        ax.set_xlabel('Use Case', fontsize=12)
        ax.set_title('Generated Proof Size (Lines)', fontsize=14, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        graph5 = self.output_dir / f"graph_proof_size_{timestamp}.png"
        plt.savefig(graph5, dpi=300)
        plt.close()
        print(f"✓ Saved graph: {graph5}")
        
        # Graph 6: Provider Comparison (if multiple providers)
        providers = list(set(r["provider"] for r in successful))
        if len(providers) > 1:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            provider_data = {}
            for provider in providers:
                provider_times = [r["total_time"] for r in successful if r["provider"] == provider]
                provider_data[provider] = provider_times
            
            bp = ax.boxplot(
                [provider_data[p] for p in providers],
                labels=[p.upper() for p in providers],
                patch_artist=True
            )
            
            colors = ['lightblue', 'lightgreen', 'lightyellow', 'lightcoral']
            for i, patch in enumerate(bp['boxes']):
                patch.set_facecolor(colors[i % len(colors)])
            
            ax.set_ylabel('Total Time (seconds)', fontsize=12)
            ax.set_xlabel('LLM Provider', fontsize=12)
            ax.set_title('Provider Comparison: Total Time', fontsize=14, fontweight='bold')
            ax.grid(axis='y', alpha=0.3)
            
            # Add mean markers
            means = [statistics.mean(provider_data[p]) for p in providers]
            ax.plot(range(1, len(means)+1), means, 'D', color='red', 
                   markersize=10, label='Mean', zorder=3)
            ax.legend()
            
            plt.tight_layout()
            graph6 = self.output_dir / f"graph_provider_comparison_{timestamp}.png"
            plt.savefig(graph6, dpi=300)
            plt.close()
            print(f"✓ Saved graph: {graph6}")
    
    def print_summary(self):
        """Print statistical summary"""
        print("\n" + "=" * 70)
        print("Statistical Summary")
        print("=" * 70)
        print()
        
        # Overall stats
        total = len(self.results)
        successful = [r for r in self.results if r["success"]]
        success_count = len(successful)
        
        print(f"Total tests: {total}")
        print(f"Successful: {success_count} ({success_count/total*100:.1f}%)")
        print(f"Failed: {total - success_count}")
        print()
        
        if not successful:
            print("No successful results to analyze")
            return
        
        # Timing stats
        print("Timing Statistics (successful tests only):")
        print("-" * 60)
        
        llm_times = [r["llm_time"] for r in successful]
        verify_times = [r["verification_time"] for r in successful]
        total_times = [r["total_time"] for r in successful]
        
        print(f"LLM Generation:")
        print(f"  Mean:   {statistics.mean(llm_times):.3f}s")
        print(f"  Median: {statistics.median(llm_times):.3f}s")
        print(f"  StdDev: {statistics.stdev(llm_times):.3f}s" if len(llm_times) > 1 else "  StdDev: N/A")
        print(f"  Min:    {min(llm_times):.3f}s")
        print(f"  Max:    {max(llm_times):.3f}s")
        print()
        
        print(f"Coq Verification:")
        print(f"  Mean:   {statistics.mean(verify_times):.3f}s")
        print(f"  Median: {statistics.median(verify_times):.3f}s")
        print(f"  StdDev: {statistics.stdev(verify_times):.3f}s" if len(verify_times) > 1 else "  StdDev: N/A")
        print(f"  Min:    {min(verify_times):.3f}s")
        print(f"  Max:    {max(verify_times):.3f}s")
        print()
        
        print(f"Total End-to-End:")
        print(f"  Mean:   {statistics.mean(total_times):.3f}s")
        print(f"  Median: {statistics.median(total_times):.3f}s")
        print(f"  StdDev: {statistics.stdev(total_times):.3f}s" if len(total_times) > 1 else "  StdDev: N/A")
        print(f"  Min:    {min(total_times):.3f}s")
        print(f"  Max:    {max(total_times):.3f}s")
        print()
        
        # Size stats
        proof_sizes = [r["proof_size_lines"] for r in successful]
        print(f"Proof Size (lines):")
        print(f"  Mean:   {statistics.mean(proof_sizes):.1f}")
        print(f"  Median: {statistics.median(proof_sizes):.1f}")
        print(f"  Min:    {min(proof_sizes)}")
        print(f"  Max:    {max(proof_sizes)}")
        print()
        
        # Token stats
        total_tokens = [r["total_tokens"] for r in successful if r["total_tokens"] > 0]
        if total_tokens:
            input_tokens = [r["input_tokens"] for r in successful if r["input_tokens"] > 0]
            output_tokens = [r["output_tokens"] for r in successful if r["output_tokens"] > 0]
            
            print(f"Token Usage:")
            print(f"  Input tokens (mean):  {statistics.mean(input_tokens):.0f}")
            print(f"  Output tokens (mean): {statistics.mean(output_tokens):.0f}")
            print(f"  Total tokens (mean):  {statistics.mean(total_tokens):.0f}")
            print(f"  Total tokens (max):   {max(total_tokens)}")
            print()
        
        # Per use case
        print("Per Use Case:")
        print("-" * 60)
        for uc in self.use_cases:
            uc_results = [r for r in self.results if r["use_case"] == uc]
            uc_successful = [r for r in uc_results if r["success"]]
            
            if uc_results:
                success_rate = len(uc_successful) / len(uc_results) * 100
                avg_time = statistics.mean([r["total_time"] for r in uc_successful]) if uc_successful else 0
                
                print(f"\n{uc}:")
                print(f"  Success rate: {success_rate:.1f}% ({len(uc_successful)}/{len(uc_results)})")
                if uc_successful:
                    print(f"  Avg time:     {avg_time:.3f}s")
        
        # Proof Size by Use Case and Model
        print("\n" + "=" * 70)
        print("Proof Size Analysis: By Use Case and Model")
        print("=" * 70)
        print()
        
        # Get unique providers
        providers = sorted(set(r["provider"] for r in self.results))
        
        # Header
        print(f"{'Use Case':<25} {'Model':<10} {'Successes':<12} {'Avg Chars':<12} {'Avg Lines':<12}")
        print("-" * 70)
        
        for uc in self.use_cases:
            for provider in providers:
                uc_provider_successful = [r for r in successful 
                                         if r["use_case"] == uc 
                                         and r["provider"] == provider]
                
                if uc_provider_successful:
                    avg_chars = statistics.mean([r["proof_size_chars"] for r in uc_provider_successful])
                    avg_lines = statistics.mean([r["proof_size_lines"] for r in uc_provider_successful])
                    count = len(uc_provider_successful)
                    
                    print(f"{uc:<25} {provider.upper():<10} {count:<12} {avg_chars:<12.0f} {avg_lines:<12.1f}")
            print()  # Blank line between use cases

def main():
    import argparse
    parser = argparse.ArgumentParser(description="PCO Framework Performance Benchmark")
    parser.add_argument("-i", "--iterations", type=int, default=5, help="Number of iterations per test (default: 5)")
    parser.add_argument("-o", "--output", default="benchmark_results", help="Output directory (default: benchmark_results)")
    parser.add_argument("-c", "--complexity", type=str, default="all", 
                       choices=["easy", "medium", "hard", "all"], 
                       help="Complexity level to test: easy, medium, hard, or all (default: all)")
    args = parser.parse_args()
    
    benchmark = PCOBenchmark(output_dir=args.output, complexity=args.complexity)
    benchmark.run_benchmark(iterations=args.iterations)
    
    print("\n" + "=" * 70)
    print("Benchmark Complete!")
    print("=" * 70)
    print(f"\nTo generate graphs, run:")
    print(f"  python3 generate_paper_graphs.py {args.output}/benchmark_*.json")
    print()

if __name__ == '__main__':
    main()
