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
            "llm_time": 0,
            "verification_time": 0,
            "total_time": 0,
            "proof_size_chars": 0,
            "proof_size_lines": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "error": None
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
            
            # Measure LLM generation
            start_llm = time.time()
            coq_code, proposition, token_info = dashboard.call_llm(prompt, api_key, provider, model)
            result["llm_time"] = time.time() - start_llm
            
            # Store token counts
            result["input_tokens"] = token_info.get("input_tokens", 0)
            result["output_tokens"] = token_info.get("output_tokens", 0)
            result["total_tokens"] = token_info.get("total_tokens", 0)
            
            # FINAL FIX: Convert old syntax to new Coq 9.0+ syntax
            import re
            
            # Convert "Require Import Coq.X.Y" to "From Stdlib Require Import X.Y"
            coq_code = re.sub(
                r'Require\s+Import\s+Coq\.([^\s.]+(?:\.[^\s.]+)*)\s*\.',
                r'From Stdlib Require Import \1.',
                coq_code
            )
            
            # Also handle any "From Coq" that slipped through
            coq_code = re.sub(
                r'From\s+Coq\s+Require\s+Import\s+([^\s.]+(?:\.[^\s.]+)*)\s*\.',
                r'From Stdlib Require Import \1.',
                coq_code
            )
            
            # Check for unterminated comments (truncation detection)
            open_comments = coq_code.count('(*')
            close_comments = coq_code.count('*)')
            if open_comments > close_comments:
                # Truncated! Try to close comments
                coq_code += '\n' + ('*)' * (open_comments - close_comments))
                print(f"    [Auto-fixed] Closed {open_comments - close_comments} unterminated comment(s)")
            
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
            if not result["success"]:
                result["error"] = verify_result.stderr[:200]
                # Keep failed file for 1 iteration to inspect
                print(f"    [Kept failed file: {proof_file.name}]")
            else:
                # Delete successful files
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
            f.write("timestamp,use_case,provider,model,success,llm_time,verification_time,total_time,proof_size_chars,proof_size_lines,input_tokens,output_tokens,total_tokens,error\n")
            # Data
            for r in self.results:
                f.write(f"{r['timestamp']},{r['use_case']},{r['provider']},{r['model']},{r['success']},{r['llm_time']:.3f},{r['verification_time']:.3f},{r['total_time']:.3f},{r['proof_size_chars']},{r['proof_size_lines']},{r['input_tokens']},{r['output_tokens']},{r['total_tokens']},\"{r['error'] or ''}\"\n")
        
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
