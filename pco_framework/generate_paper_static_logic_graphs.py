#!/usr/bin/env python3
"""
Generate publication-quality graphs for academic papers

Creates:
- High-resolution graphs (300 DPI)
- LaTeX-ready tables
- Statistical comparisons
- Performance analysis
"""

import json
import sys
from pathlib import Path
import statistics

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.serif'] = ['Times New Roman', 'Times', 'DejaVu Serif']
    plt.rcParams['font.size'] = 10
except ImportError:
    print("Error: matplotlib required")
    print("Install: pip install matplotlib")
    sys.exit(1)

def load_results(results_file):
    """Load benchmark results from JSON"""
    with open(results_file) as f:
        return json.load(f)

def generate_comparison_table(results, output_file="table_comparison.tex"):
    """Generate LaTeX table comparing use cases"""
    
    use_cases = ["tax_compliance", "autonomous_vehicle", "consumer_protection"]
    
    # Calculate statistics per use case
    stats = {}
    for uc in use_cases:
        uc_results = [r for r in results if r["use_case"] == uc and r["success"]]
        
        if uc_results:
            stats[uc] = {
                "success_rate": len(uc_results) / len([r for r in results if r["use_case"] == uc]) * 100,
                "llm_mean": statistics.mean([r["llm_time"] for r in uc_results]),
                "llm_std": statistics.stdev([r["llm_time"] for r in uc_results]) if len(uc_results) > 1 else 0,
                "verify_mean": statistics.mean([r["verification_time"] for r in uc_results]),
                "verify_std": statistics.stdev([r["verification_time"] for r in uc_results]) if len(uc_results) > 1 else 0,
                "total_mean": statistics.mean([r["total_time"] for r in uc_results]),
                "total_std": statistics.stdev([r["total_time"] for r in uc_results]) if len(uc_results) > 1 else 0,
                "proof_lines": statistics.mean([r["proof_size_lines"] for r in uc_results]),
            }
    
    # Generate LaTeX table
    latex = []
    latex.append("\\begin{table}[h]")
    latex.append("\\centering")
    latex.append("\\caption{PCO Framework Performance by Use Case}")
    latex.append("\\label{tab:pco_performance}")
    latex.append("\\begin{tabular}{lccccc}")
    latex.append("\\hline")
    latex.append("\\textbf{Use Case} & \\textbf{Success} & \\textbf{LLM (s)} & \\textbf{Verify (s)} & \\textbf{Total (s)} & \\textbf{LOC} \\\\")
    latex.append("\\hline")
    
    labels = {
        "tax_compliance": "Tax Compliance",
        "autonomous_vehicle": "Autonomous Vehicle",
        "consumer_protection": "Consumer Protection"
    }
    
    for uc in use_cases:
        if uc in stats:
            s = stats[uc]
            latex.append(f"{labels[uc]} & "
                        f"{s['success_rate']:.1f}\\% & "
                        f"{s['llm_mean']:.2f} $\\pm$ {s['llm_std']:.2f} & "
                        f"{s['verify_mean']:.2f} $\\pm$ {s['verify_std']:.2f} & "
                        f"{s['total_mean']:.2f} $\\pm$ {s['total_std']:.2f} & "
                        f"{s['proof_lines']:.0f} \\\\")
    
    latex.append("\\hline")
    latex.append("\\end{tabular}")
    latex.append("\\end{table}")
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(latex))
    
    print(f"✓ Generated LaTeX table: {output_file}")
    return latex

def generate_size_table(results, output_file="table_proof_sizes.tex"):
    """Generate LaTeX table showing proof sizes by use case and model"""
    
    use_cases = ["tax_compliance", "autonomous_vehicle", "consumer_protection"]
    successful = [r for r in results if r["success"]]
    
    # Get unique providers
    providers = sorted(set(r["provider"] for r in successful))
    
    # Calculate statistics per use case per provider
    stats = {}
    for uc in use_cases:
        stats[uc] = {}
        for provider in providers:
            uc_provider_results = [r for r in successful 
                                  if r["use_case"] == uc 
                                  and r["provider"] == provider]
            
            if uc_provider_results:
                stats[uc][provider] = {
                    "count": len(uc_provider_results),
                    "chars_mean": statistics.mean([r["proof_size_chars"] for r in uc_provider_results]),
                    "lines_mean": statistics.mean([r["proof_size_lines"] for r in uc_provider_results]),
                }
    
    # Generate LaTeX table
    latex = []
    latex.append("\\begin{table}[h]")
    latex.append("\\centering")
    latex.append("\\caption{Proof Size Analysis: By Use Case and Model}")
    latex.append("\\label{tab:proof_sizes}")
    
    # Header with provider columns
    header = "\\begin{tabular}{l" + "c" * (len(providers) * 2) + "}"
    latex.append(header)
    latex.append("\\hline")
    
    # Column headers
    col_headers = "\\textbf{Use Case}"
    for provider in providers:
        col_headers += f" & \\multicolumn{{2}}{{c}}{{\\textbf{{{provider.upper()}}}}}"
    col_headers += " \\\\"
    latex.append(col_headers)
    
    # Sub-headers (Chars / Lines)
    subheaders = ""
    for _ in providers:
        subheaders += " & \\textbf{Chars} & \\textbf{Lines}"
    latex.append(subheaders + " \\\\")
    latex.append("\\hline")
    
    labels = {
        "tax_compliance": "Tax Compliance",
        "autonomous_vehicle": "Autonomous Vehicle",
        "consumer_protection": "Consumer Protection"
    }
    
    # Data rows
    for uc in use_cases:
        row = labels[uc]
        for provider in providers:
            if provider in stats[uc]:
                s = stats[uc][provider]
                row += f" & {s['chars_mean']:.0f} & {s['lines_mean']:.1f}"
            else:
                row += " & --- & ---"
        row += " \\\\"
        latex.append(row)
    
    latex.append("\\hline")
    latex.append("\\end{tabular}")
    latex.append("\\end{table}")
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(latex))
    
    print(f"✓ Generated proof size table: {output_file}")
    return latex

def generate_paper_graph_timing(results, output_file="figure_timing.pdf"):
    """Generate stacked bar chart: LLM time + Coq time in different colors"""
    
    use_cases = ["tax_compliance", "autonomous_vehicle", "consumer_protection"]
    labels = ["Tax\nCompliance", "Autonomous\nVehicle", "Consumer\nProtection"]
    
    # Get unique providers (simplified: just OpenAI, Gemini, Claude)
    providers = []
    for r in results:
        if r['provider'] not in providers:
            providers.append(r['provider'])
    
    # Always use grouped bars: Use Cases × LLM Providers
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = range(len(labels))
    n_providers = len(providers)
    width = 0.8 / n_providers  # Bars per use case
    
    # Provider colors (matching paper figure style)
    provider_colors = {
        'openai': '#2E8B57',      # Green (OAI)
        'claude': '#E67E22',      # Orange (Cla)
        'gemini': '#4169E1',      # Blue/Purple (Gem)
        'groq': '#000000',        # Black (Grq)
        'deepseek': '#87CEEB',    # Light Blue (DS)
    }
    
    # For each provider, plot STACKED bars (LLM + Coq)
    # Use SUCCESS-ONLY metrics to avoid outliers from retries
    for i, provider in enumerate(providers):
        llm_means = []
        coq_means = []
        
        for uc in use_cases:
            # Get results for this use case and provider
            uc_provider_results = [r for r in results 
                                  if r["use_case"] == uc 
                                  and r['provider'] == provider
                                  and r["success"]]
            if uc_provider_results:
                # Use success_llm_time if available (only the successful attempt)
                # Otherwise fall back to llm_time
                llm_times = [r.get("success_llm_time", r["llm_time"]) for r in uc_provider_results]
                verify_times = [r.get("success_verify_time", r["verification_time"]) for r in uc_provider_results]
                llm_means.append(statistics.mean(llm_times))
                coq_means.append(statistics.mean(verify_times))
            else:
                llm_means.append(0)
                coq_means.append(0)
        
        # Calculate offset for this provider
        offset = (i - n_providers/2 + 0.5) * width
        positions = [xi + offset for xi in x]
        
        # Get colors for this provider
        base_color = provider_colors.get(provider, '#888888')
        
        # Plot LLM time (bottom, darker)
        llm_bars = ax.bar(positions, llm_means, width, 
                         label=provider.capitalize(), 
                         color=base_color, 
                         edgecolor='black', linewidth=0.5)
        
        # Plot Coq time (top, lighter - same hue but alpha blended with hatching)
        coq_bars = ax.bar(positions, coq_means, width, 
                         bottom=llm_means,
                         label='Coq Verification' if i == 0 else '',  # Only show once
                         color=base_color, alpha=0.4,
                         edgecolor='black', linewidth=0.5,
                         hatch='///')
        
        # Add total time labels on top
        for j, (llm_bar, coq_bar) in enumerate(zip(llm_bars, coq_bars)):
            total_height = llm_means[j] + coq_means[j]
            if total_height > 0:
                ax.text(llm_bar.get_x() + llm_bar.get_width()/2., total_height,
                       f'{total_height:.1f}s',
                       ha='center', va='bottom', fontsize=7, fontweight='bold')
    
    ax.set_ylabel('Time (seconds)', fontweight='bold', fontsize=12)
    ax.set_xlabel('Use Case', fontweight='bold', fontsize=12)
    ax.set_title('PCO Framework: LLM Generation + Coq Verification Time', fontweight='bold', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    
    # Organize legend: LLM providers + Coq verification
    handles, legend_labels = ax.get_legend_handles_labels()
    ax.legend(handles, legend_labels, loc='upper left', fontsize=9, ncol=2, 
              title='LLM Providers | Hatched = Coq', title_fontsize=9)
    
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    # Save as PDF (vector format for papers)
    plt.savefig(output_file.replace('.pdf', '.pdf'), format='pdf', dpi=300, bbox_inches='tight')
    # Also save as PNG
    plt.savefig(output_file.replace('.pdf', '.png'), format='png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Generated figure: {output_file} (PDF and PNG)")

def generate_paper_graph_success_rate(results, output_file="figure_success.pdf"):
    """Generate grouped success rate: all use cases × all LLM providers"""
    
    use_cases = ["tax_compliance", "autonomous_vehicle", "consumer_protection"]
    labels = ["Tax\nCompliance", "Autonomous\nVehicle", "Consumer\nProtection"]
    
    # Get unique providers (simplified)
    providers = []
    for r in results:
        if r['provider'] not in providers:
            providers.append(r['provider'])
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = range(len(labels))
    n_providers = len(providers)
    width = 0.8 / n_providers
    
    provider_colors = {
        'openai': '#2E8B57',      # Green (OAI)
        'claude': '#E67E22',      # Orange (Cla)
        'gemini': '#4169E1',      # Blue/Purple (Gem)
        'groq': '#000000',        # Black (Grq)
        'deepseek': '#87CEEB',    # Light Blue (DS)
    }
    
    # For each provider
    for i, provider in enumerate(providers):
        success_rates = []
        for uc in use_cases:
            uc_provider_results = [r for r in results 
                                  if r["use_case"] == uc 
                                  and r['provider'] == provider]
            if uc_provider_results:
                success_count = sum(1 for r in uc_provider_results if r["success"])
                rate = (success_count / len(uc_provider_results)) * 100
            else:
                rate = 0
            success_rates.append(rate)
        
        offset = (i - n_providers/2 + 0.5) * width
        color = provider_colors.get(provider, '#888888')
        bars = ax.bar([xi + offset for xi in x], success_rates, width,
                     label=provider.capitalize(), color=color,
                     edgecolor='black', linewidth=1)
        
        # Add percentage labels
        for bar, rate in zip(bars, success_rates):
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                       f'{rate:.0f}%',
                       ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    ax.set_ylabel('Success Rate (%)', fontweight='bold', fontsize=12)
    ax.set_xlabel('Use Case', fontweight='bold', fontsize=12)
    ax.set_title('PCO Framework: Success Rate by LLM Provider', fontweight='bold', fontsize=14)
    ax.set_ylim(0, 110)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.legend(title='LLM Provider', loc='lower right', fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add horizontal line at 100%
    ax.axhline(y=100, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
    
    plt.tight_layout()
    
    plt.savefig(output_file.replace('.pdf', '.pdf'), format='pdf', dpi=300, bbox_inches='tight')
    plt.savefig(output_file.replace('.pdf', '.png'), format='png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Generated figure: {output_file} (PDF and PNG)")

def generate_paper_graph_boxplot(results, output_file="figure_distribution.pdf"):
    """Generate box plot showing time distribution"""
    
    use_cases = ["tax_compliance", "autonomous_vehicle", "consumer_protection"]
    labels = ["Tax\nCompliance", "Autonomous\nVehicle", "Consumer\nProtection"]
    
    data = []
    for uc in use_cases:
        uc_successful = [r for r in results if r["use_case"] == uc and r["success"]]
        times = [r["total_time"] for r in uc_successful]
        data.append(times if times else [0])
    
    fig, ax = plt.subplots(figsize=(6, 4))
    
    bp = ax.boxplot(data, labels=labels, patch_artist=True,
                    boxprops=dict(facecolor='lightblue', color='black'),
                    whiskerprops=dict(color='black'),
                    capprops=dict(color='black'),
                    medianprops=dict(color='red', linewidth=2))
    
    ax.set_ylabel('Total Time (seconds)', fontweight='bold')
    ax.set_xlabel('Use Case', fontweight='bold')
    ax.set_title('PCO Framework: Time Distribution', fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    plt.savefig(output_file.replace('.pdf', '.pdf'), format='pdf', dpi=300, bbox_inches='tight')
    plt.savefig(output_file.replace('.pdf', '.png'), format='png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Generated figure: {output_file} (PDF and PNG)")

def generate_paper_summary(results, output_file="paper_summary.txt"):
    """Generate text summary suitable for paper"""
    
    successful = [r for r in results if r["success"]]
    
    lines = []
    lines.append("=" * 70)
    lines.append("PCO FRAMEWORK PERFORMANCE SUMMARY (FOR PAPER)")
    lines.append("=" * 70)
    lines.append("")
    
    # Overall statistics
    total = len(results)
    success_count = len(successful)
    
    lines.append("OVERALL PERFORMANCE")
    lines.append("-" * 70)
    lines.append(f"Total evaluations: {total}")
    lines.append(f"Successful proofs: {success_count} ({success_count/total*100:.1f}%)")
    lines.append("")
    
    if not successful:
        with open(output_file, 'w') as f:
            f.write('\n'.join(lines))
        return
    
    # Timing statistics
    llm_times = [r["llm_time"] for r in successful]
    verify_times = [r["verification_time"] for r in successful]
    total_times = [r["total_time"] for r in successful]
    
    lines.append("TIMING STATISTICS")
    lines.append("-" * 70)
    lines.append(f"LLM Generation:    {statistics.mean(llm_times):.2f} ± {statistics.stdev(llm_times):.2f}s (mean ± std)")
    lines.append(f"Coq Verification:  {statistics.mean(verify_times):.2f} ± {statistics.stdev(verify_times):.2f}s")
    lines.append(f"Total End-to-End:  {statistics.mean(total_times):.2f} ± {statistics.stdev(total_times):.2f}s")
    lines.append("")
    
    # Per use case
    use_cases = ["tax_compliance", "autonomous_vehicle", "consumer_protection"]
    names = {"tax_compliance": "Tax Compliance",
             "autonomous_vehicle": "Autonomous Vehicle Safety",
             "consumer_protection": "Consumer Protection"}
    
    lines.append("PER USE CASE ANALYSIS")
    lines.append("-" * 70)
    
    for uc in use_cases:
        uc_results = [r for r in results if r["use_case"] == uc]
        uc_successful = [r for r in uc_results if r["success"]]
        
        if uc_results:
            lines.append(f"\n{names[uc]}:")
            lines.append(f"  Success rate: {len(uc_successful)/len(uc_results)*100:.1f}%")
            
            if uc_successful:
                avg_llm = statistics.mean([r["llm_time"] for r in uc_successful])
                avg_verify = statistics.mean([r["verification_time"] for r in uc_successful])
                avg_total = statistics.mean([r["total_time"] for r in uc_successful])
                avg_lines = statistics.mean([r["proof_size_lines"] for r in uc_successful])
                
                lines.append(f"  LLM time:     {avg_llm:.2f}s")
                lines.append(f"  Verify time:  {avg_verify:.2f}s")
                lines.append(f"  Total time:   {avg_total:.2f}s")
                lines.append(f"  Proof size:   {avg_lines:.0f} lines")
    
    lines.append("")
    lines.append("=" * 70)
    lines.append("")
    lines.append("SUGGESTED TEXT FOR PAPER:")
    lines.append("-" * 70)
    lines.append("")
    lines.append(f"We evaluated the PCO framework across {len(use_cases)} regulatory use cases ")
    lines.append(f"(tax compliance, autonomous vehicle safety, and consumer protection) with ")
    lines.append(f"{len(results)} total proof generation attempts. The framework achieved a ")
    lines.append(f"{success_count/total*100:.1f}% success rate in generating valid, compilable ")
    lines.append(f"Coq proofs. The average end-to-end time from LLM query to verified proof ")
    lines.append(f"was {statistics.mean(total_times):.2f} ± {statistics.stdev(total_times):.2f} seconds, ")
    lines.append(f"with LLM generation accounting for {statistics.mean(llm_times):.2f}s and ")
    lines.append(f"Coq verification taking {statistics.mean(verify_times):.2f}s on average.")
    
    with open(output_file, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"✓ Generated summary: {output_file}")

def generate_provider_comparison_graph(results, output_file="figure_provider_comparison.pdf"):
    """Generate graph comparing all providers and models"""
    
    # Get all provider/model combinations
    provider_models = {}
    for r in results:
        key = f"{r['provider']}/{r['model'].split('-')[-1]}"  # e.g., "claude/haiku", "openai/4"
        if key not in provider_models:
            provider_models[key] = []
        if r["success"]:
            provider_models[key].append(r["total_time"])
    
    if not provider_models:
        print("⚠ No successful results for provider comparison")
        return
    
    # Sort by mean time
    sorted_providers = sorted(provider_models.items(), 
                             key=lambda x: statistics.mean(x[1]) if x[1] else 0)
    
    labels = [p[0].replace('/', '\n') for p in sorted_providers]
    data = [p[1] for p in sorted_providers]
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Box plot
    bp = ax.boxplot(data, labels=labels, patch_artist=True)
    
    colors = ['#2E8B57', '#E67E22', '#4169E1', '#000000', '#87CEEB']  # OAI, Cla, Gem, Grq, DS
    for i, patch in enumerate(bp['boxes']):
        patch.set_facecolor(colors[i % len(colors)])
    
    # Style
    for median in bp['medians']:
        median.set(color='red', linewidth=2)
    
    ax.set_ylabel('Total Time (seconds)', fontweight='bold')
    ax.set_xlabel('LLM Provider / Model', fontweight='bold')
    ax.set_title('PCO Framework: LLM Provider & Model Comparison', fontweight='bold')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add mean markers
    means = [statistics.mean(d) for d in data]
    ax.plot(range(1, len(means)+1), means, 'D', color='black', 
            markersize=8, label='Mean', zorder=3)
    
    ax.legend(loc='upper right')
    
    plt.tight_layout()
    plt.savefig(output_file.replace('.pdf', '.pdf'), format='pdf', dpi=300, bbox_inches='tight')
    plt.savefig(output_file.replace('.pdf', '.png'), format='png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Generated figure: {output_file} (PDF and PNG)")

def generate_proof_size_graph(results, output_file="figure_proof_sizes.pdf"):
    """Generate grouped bar chart: proof sizes by use case × LLM provider"""
    
    use_cases = ["tax_compliance", "autonomous_vehicle", "consumer_protection"]
    labels = ["Tax\nCompliance", "Autonomous\nVehicle", "Consumer\nProtection"]
    
    # Get successful results only
    successful = [r for r in results if r["success"]]
    
    if not successful:
        print("⚠ No successful results for proof size graph")
        return
    
    # Get unique providers (simplified)
    providers = []
    for r in successful:
        if r['provider'] not in providers:
            providers.append(r['provider'])
    
    # Prepare data: use_case -> provider -> lines
    data_lines = {}
    
    for uc in use_cases:
        data_lines[uc] = {}
        for provider in providers:
            uc_provider_results = [r for r in successful 
                                  if r["use_case"] == uc 
                                  and r['provider'] == provider]
            
            if uc_provider_results:
                data_lines[uc][provider] = statistics.mean([r["proof_size_lines"] for r in uc_provider_results])
            else:
                data_lines[uc][provider] = 0
    
    # Create single figure (ONLY Lines of Code)
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = range(len(labels))
    n_providers = len(providers)
    width = 0.8 / n_providers
    
    provider_colors = {
        'openai': '#2E8B57',      # Green (OAI)
        'claude': '#E67E22',      # Orange (Cla)
        'gemini': '#4169E1',      # Blue/Purple (Gem)
        'groq': '#000000',        # Black (Grq)
        'deepseek': '#87CEEB',    # Light Blue (DS)
    }
    
    # Plot Lines of Code
    for i, provider in enumerate(providers):
        provider_label = provider.capitalize()
        heights = [data_lines[uc][provider] for uc in use_cases]
        positions = [pos + (i - n_providers/2 + 0.5) * width for pos in x]
        
        color = provider_colors.get(provider, '#888888')
        bars = ax.bar(positions, heights, width, 
                      label=provider_label,
                      color=color,
                      edgecolor='black', linewidth=0.5)
        
        # Add value labels on bars
        for bar, height in zip(bars, heights):
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.0f}',
                        ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    ax.set_ylabel('Lines of Code', fontweight='bold', fontsize=13)
    ax.set_xlabel('Use Case', fontweight='bold', fontsize=13)
    ax.set_title('PCO Framework: Proof Size Comparison', fontweight='bold', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=12)
    ax.legend(title='LLM Provider', loc='upper left', fontsize=10, title_fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    
    plt.savefig(output_file.replace('.pdf', '.pdf'), format='pdf', dpi=300, bbox_inches='tight')
    plt.savefig(output_file.replace('.pdf', '.png'), format='png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Generated figure: {output_file} (PDF and PNG)")

def generate_token_count_graph(results, output_file="figure_tokens.pdf"):
    """Generate token usage comparison by use case × LLM provider"""
    
    use_cases = ["tax_compliance", "autonomous_vehicle", "consumer_protection"]
    labels = ["Tax\nCompliance", "Autonomous\nVehicle", "Consumer\nProtection"]
    
    # Get successful results only
    successful = [r for r in results if r["success"]]
    
    if not successful:
        print("⚠ No successful results for token graph")
        return
    
    # Check if token counts exist in data
    if "total_tokens" not in successful[0]:
        print("⚠ Token count data not available in results (run new benchmark to get tokens)")
        return
    
    # Get unique providers (simplified)
    providers = []
    for r in successful:
        if r['provider'] not in providers:
            providers.append(r['provider'])
    
    # Prepare data: use_case -> provider -> tokens
    data_input = {}
    data_output = {}
    data_total = {}
    
    for uc in use_cases:
        data_input[uc] = {}
        data_output[uc] = {}
        data_total[uc] = {}
        
        for provider in providers:
            uc_provider_results = [r for r in successful 
                                  if r["use_case"] == uc 
                                  and r['provider'] == provider]
            
            if uc_provider_results:
                # Calculate average tokens - use SUCCESS-ONLY tokens to avoid outliers
                # success_tokens = only the successful attempt, not wasted retries
                success_tokens = [r.get("success_tokens", r["total_tokens"]) for r in uc_provider_results]
                avg_total_tokens = statistics.mean(success_tokens)
                
                # For input/output breakdown, estimate from ratio if not tracked separately
                avg_input_tokens = statistics.mean([r["input_tokens"] for r in uc_provider_results])
                avg_output_tokens = statistics.mean([r["output_tokens"] for r in uc_provider_results])
                
                # Scale to success-only if we have success_tokens
                if "success_tokens" in uc_provider_results[0]:
                    total_all = statistics.mean([r["total_tokens"] for r in uc_provider_results])
                    if total_all > 0:
                        ratio = avg_total_tokens / total_all
                        avg_input_tokens *= ratio
                        avg_output_tokens *= ratio
                
                data_input[uc][provider] = avg_input_tokens
                data_output[uc][provider] = avg_output_tokens
                data_total[uc][provider] = avg_total_tokens
            else:
                data_input[uc][provider] = 0
                data_output[uc][provider] = 0
                data_total[uc][provider] = 0
    
    # Create single figure with stacked bars (input + output tokens)
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = range(len(labels))
    n_providers = len(providers)
    width = 0.8 / n_providers
    
    provider_colors = {
        'openai': '#2E8B57',      # Green (OAI)
        'claude': '#E67E22',      # Orange (Cla)
        'gemini': '#4169E1',      # Blue/Purple (Gem)
        'groq': '#000000',        # Black (Grq)
        'deepseek': '#87CEEB',    # Light Blue (DS)
    }
    
    # Stacked bars (input + output tokens)
    for i, provider in enumerate(providers):
        provider_label = provider.capitalize()
        input_heights = [data_input[uc][provider] for uc in use_cases]
        output_heights = [data_output[uc][provider] for uc in use_cases]
        positions = [pos + (i - n_providers/2 + 0.5) * width for pos in x]
        
        color = provider_colors.get(provider, '#888888')
        
        # Plot input tokens (bottom)
        ax.bar(positions, input_heights, width, 
               label=f'{provider_label}',
               color=color,
               edgecolor='black', linewidth=0.5)
        
        # Plot output tokens (top)
        ax.bar(positions, output_heights, width, 
               bottom=input_heights,
               color=color, alpha=0.6,
               hatch='///',
               edgecolor='black', linewidth=0.5)
        
        # Add total labels on top of stacked bars
        for pos, inp, out in zip(positions, input_heights, output_heights):
            total = inp + out
            if total > 0:
                # Format token count with K suffix for thousands
                if total >= 1000:
                    label = f'{total/1000:.1f}K'
                else:
                    label = f'{int(total)}'
                ax.text(pos, total, label,
                        ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    ax.set_ylabel('Token Count', fontweight='bold', fontsize=11)
    ax.set_xlabel('Use Case', fontweight='bold', fontsize=11)
    ax.set_title('Token Usage: Input + Output (Stacked)', fontweight='bold', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Create custom legend for stacked bars
    from matplotlib.patches import Patch
    legend_elements = []
    for provider in providers:
        color = provider_colors.get(provider, '#888888')
        legend_elements.append(Patch(facecolor=color, edgecolor='black', label=provider.capitalize()))
    legend_elements.append(Patch(facecolor='white', hatch='///', edgecolor='black', label='Output Tokens'))
    ax.legend(handles=legend_elements, loc='upper left', fontsize=9)
    
    plt.tight_layout()
    
    plt.savefig(output_file.replace('.pdf', '.pdf'), format='pdf', dpi=300, bbox_inches='tight')
    plt.savefig(output_file.replace('.pdf', '.png'), format='png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Generated token count figure: {output_file} (PDF and PNG)")

def generate_complexity_success_graph(results, output_dir="paper_figures"):
    """
    Generate single success rate graph with all data
    Structure: 2 use cases × 3 complexities × 5 models = 30 bars
    Grouped by: Use Case → Complexity → Model
    Each model gets its own color (consistent across all graphs)
    Note: AV disabled (will test with SLM later)
    """
    import numpy as np
    
    use_cases = ["tax", "recommendation"]  # AV disabled - will test with SLM later
    use_case_names = {
        "tax": "Tax",
        # "av": "AV",  # DISABLED
        "recommendation": "Rec"
    }
    providers = ["openai", "claude", "gemini", "groq", "deepseek"]  # 5 models
    num_models = len(providers)
    provider_names = {
        "openai": "OAI", 
        "claude": "Cla", 
        "gemini": "Gem",
        "groq": "Grq",
        "deepseek": "DS"
    }
    complexity_order = ['easy', 'medium', 'hard']
    complexity_names = {"easy": "Easy", "medium": "Med", "hard": "Hard"}
    
    # Colors by model (matching paper figure style)
    model_colors = {
        'openai': '#2E8B57',    # Green (OAI)
        'claude': '#E67E22',    # Orange (Cla)
        'gemini': '#4169E1',    # Blue/Purple (Gem)
        'groq': '#000000',      # Black (Grq)
        'deepseek': '#87CEEB',  # Light Blue (DS)
    }
    
    # Group results
    data = {}
    for result in results:
        use_case = result.get("use_case_type", "unknown")
        if use_case not in use_cases:
            continue
            
        provider = result["provider"]
        if provider not in providers:
            continue
            
        complexity = result.get("complexity", "medium")
        
        key = (use_case, complexity, provider)
        if key not in data:
            data[key] = []
        data[key].append(result["success"])
    
    # Calculate success rates and positions with spacing
    success_rates = []
    colors = []
    x_positions = []
    
    bar_width = 0.5
    model_spacing = 0.1        # Small gap between models
    complexity_spacing = 1.2   # Medium gap between complexities
    usecase_spacing = 2.5      # Large gap between use cases
    
    current_x = 0
    for i, use_case in enumerate(use_cases):
        if i > 0:
            current_x += usecase_spacing
        
        for j, complexity in enumerate(complexity_order):
            if j > 0:
                current_x += complexity_spacing
            
            for k, provider in enumerate(providers):
                if k > 0:
                    current_x += model_spacing
                
                key = (use_case, complexity, provider)
                if key in data and data[key]:
                    rate = sum(data[key]) / len(data[key]) * 100
                else:
                    rate = 0
                
                success_rates.append(rate)
                colors.append(model_colors[provider])
                x_positions.append(current_x)
                current_x += bar_width
    
    # Create figure
    fig, ax = plt.subplots(figsize=(7, 4.5))
    
    bars = ax.bar(x_positions, success_rates, width=bar_width, 
                  color=colors, edgecolor='black', linewidth=0.3)
    
    # Add value labels
    for bar, rate in zip(bars, success_rates):
        if rate > 5:
            ax.text(bar.get_x() + bar.get_width()/2., rate + 2,
                   f'{rate:.0f}',
                   ha='center', va='bottom', fontsize=7)
    
    ax.set_ylabel('Success Rate (%)', fontsize=13, fontweight='bold')
    ax.set_ylim([0, 108])
    
    # X-axis: Complexity labels
    num_models = len(providers)
    complexity_centers = []
    idx = 0
    for i, use_case in enumerate(use_cases):
        for j, complexity in enumerate(complexity_order):
            # Center of model bars for this complexity
            center = (x_positions[idx] + x_positions[idx+num_models-1]) / 2
            complexity_centers.append(center)
            idx += num_models
    
    ax.set_xticks(complexity_centers)
    ax.set_xticklabels([complexity_names[c] for c in complexity_order] * len(use_cases), 
                       fontsize=9, rotation=0)
    
    # Add use case labels (no background)
    for i, use_case in enumerate(use_cases):
        start_idx = i * (3 * num_models)  # 3 complexities × num_models
        center = (x_positions[start_idx] + x_positions[start_idx + (3 * num_models) - 1]) / 2
        ax.text(center, -12, use_case_names[use_case].upper(), 
               ha='center', va='top', fontsize=11, fontweight='bold')
    
    # Add vertical separators between use cases (thick)
    for i in range(1, len(use_cases)):
        sep_x = (x_positions[i*(3*num_models) - 1] + bar_width/2 + x_positions[i*(3*num_models)]) / 2
        ax.axvline(x=sep_x, color='black', linestyle='-', linewidth=1.5, alpha=0.7)
    
    # Add vertical separators between complexities (medium)
    num_models = len(providers)
    for i in range(len(use_cases)):
        for j in range(1, len(complexity_order)):
            idx = i * (3 * num_models) + j * num_models
            if idx > 0 and idx < len(x_positions):
                sep_x = (x_positions[idx - 1] + bar_width/2 + x_positions[idx]) / 2
                ax.axvline(x=sep_x, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
    
    # Legend removed (not needed for paper figure)
    
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.axhline(y=100, color='gray', linestyle=':', linewidth=0.8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    output_dir = Path(output_dir)
    output_file = output_dir / "figure_complexity_success_all.pdf"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.savefig(str(output_file).replace('.pdf', '.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Saved: {output_file}")


def generate_complexity_runtime_graph(results, output_dir="paper_figures"):
    """
    Generate single runtime graph with all data
    Structure: 2 use cases × 3 complexities × 4 models = 24 bars
    Grouped by: Use Case → Complexity → Model
    Each model gets its own color (consistent across all graphs)
    Note: Groq disabled due to rate limits, AV disabled (will test with SLM later)
    """
    import numpy as np
    
    use_cases = ["tax", "recommendation"]  # AV disabled - will test with SLM later
    use_case_names = {
        "tax": "Tax",
        # "av": "AV",  # DISABLED
        "recommendation": "Rec"
    }
    providers = ["openai", "claude", "gemini", "groq", "deepseek"]  # 5 models
    num_models = len(providers)
    provider_names = {
        "openai": "OAI", 
        "claude": "Cla", 
        "gemini": "Gem",
        "groq": "Grq",
        "deepseek": "DS"
    }
    complexity_order = ['easy', 'medium', 'hard']
    complexity_names = {"easy": "Easy", "medium": "Med", "hard": "Hard"}
    
    # Colors by model (matching paper figure style)
    model_colors = {
        'openai': '#2E8B57',    # Green (OAI)
        'claude': '#E67E22',    # Orange (Cla)
        'gemini': '#4169E1',    # Blue/Purple (Gem)
        'groq': '#000000',      # Black (Grq)
        'deepseek': '#87CEEB',  # Light Blue (DS)
    }
    
    # Collect LLM and Coq times separately for stacked bars
    llm_data = {}
    coq_data = {}
    
    for result in results:
        if not result.get("success", False):
            continue
            
        use_case = result.get("use_case_type", result.get("use_case", "unknown"))
        if use_case not in use_cases:
            continue
            
        provider = result["provider"]
        if provider not in providers:
            continue
            
        complexity = result.get("complexity", "medium")
        
        key = (use_case, complexity, provider)
        if key not in llm_data:
            llm_data[key] = []
            coq_data[key] = []
        # Use SUCCESS-ONLY metrics to avoid outliers from retries
        llm_data[key].append(result.get("success_llm_time", result.get("llm_time", 0)))
        coq_data[key].append(result.get("success_verify_time", result.get("verification_time", 0)))
    
    # Calculate mean times and positions
    llm_times = []
    coq_times = []
    colors = []
    x_positions = []
    
    bar_width = 0.5
    model_spacing = 0.1
    complexity_spacing = 1.2
    usecase_spacing = 2.5
    
    current_x = 0
    for i, use_case in enumerate(use_cases):
        if i > 0:
            current_x += usecase_spacing
        
        for j, complexity in enumerate(complexity_order):
            if j > 0:
                current_x += complexity_spacing
            
            for k, provider in enumerate(providers):
                if k > 0:
                    current_x += model_spacing
                
                key = (use_case, complexity, provider)
                if key in llm_data and llm_data[key]:
                    mean_llm = statistics.mean(llm_data[key])
                    mean_coq = statistics.mean(coq_data[key])
                else:
                    mean_llm = 0
                    mean_coq = 0
                
                llm_times.append(mean_llm)
                coq_times.append(mean_coq)
                colors.append(model_colors[provider])
                x_positions.append(current_x)
                current_x += bar_width
    
    # Create figure with stacked bars
    fig, ax = plt.subplots(figsize=(7, 4.5))
    
    # Stack: LLM time (bottom, solid) + Coq time (top, hatched with white lines)
    bars_llm = ax.bar(x_positions, llm_times, width=bar_width, 
                      color=colors, edgecolor='black', linewidth=0.3)
    
    # Hatched bars with white diagonal lines
    import matplotlib.patches as mpatches
    mpatches.Patch(facecolor='none', edgecolor='white', hatch='///')
    bars_coq = ax.bar(x_positions, coq_times, width=bar_width, bottom=llm_times,
                      color=colors, edgecolor='white', linewidth=0.5, 
                      hatch='////', zorder=3)
    # Set hatch color to white
    for bar in bars_coq:
        bar.set_edgecolor('white')
    
    # Add total time labels
    max_runtime = max([l + c for l, c in zip(llm_times, coq_times)]) if llm_times else 1
    for x, llm_t, coq_t in zip(x_positions, llm_times, coq_times):
        total_t = llm_t + coq_t
        if total_t > max_runtime * 0.05:
            ax.text(x, total_t,
                   f'{total_t:.1f}',
                   ha='center', va='bottom', fontsize=7)
    
    ax.set_ylabel('Time (seconds)', fontsize=13, fontweight='bold')
    ax.set_ylim([0, max_runtime * 1.08])
    
    # X-axis: Complexity labels (calculate from actual x_positions)
    complexity_centers = []
    idx = 0
    for i, use_case in enumerate(use_cases):
        for j, complexity in enumerate(complexity_order):
            # Center of model bars for this complexity
            if idx + num_models - 1 < len(x_positions):
                center = (x_positions[idx] + x_positions[idx+num_models-1]) / 2
                complexity_centers.append(center)
            idx += num_models
    
    ax.set_xticks(complexity_centers)
    ax.set_xticklabels([complexity_names[c] for c in complexity_order] * len(use_cases), 
                       fontsize=9, rotation=0)
    
    # Add use case labels (no background)
    for i, use_case in enumerate(use_cases):
        start_idx = i * (3 * num_models)  # 3 complexities × num_models
        end_idx = start_idx + (3 * num_models) - 1
        if end_idx < len(x_positions):
            center = (x_positions[start_idx] + x_positions[end_idx]) / 2
            ax.text(center, -max_runtime * 0.12, use_case_names[use_case].upper(), 
                   ha='center', va='top', fontsize=11, fontweight='bold')
    
    # Add vertical separators between use cases (thick)
    for i in range(1, len(use_cases)):
        sep_idx = i*(3*num_models)
        if sep_idx < len(x_positions) and sep_idx > 0:
            sep_x = (x_positions[sep_idx - 1] + bar_width/2 + x_positions[sep_idx]) / 2
            ax.axvline(x=sep_x, color='black', linestyle='-', linewidth=1.5, alpha=0.7)
    
    # Add vertical separators between complexities (medium)
    for i in range(len(use_cases)):
        for j in range(1, len(complexity_order)):
            idx = i * (3 * num_models) + j * num_models
            if idx > 0 and idx < len(x_positions):
                sep_x = (x_positions[idx - 1] + bar_width/2 + x_positions[idx]) / 2
                ax.axvline(x=sep_x, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
    
    # Legend: Models + Coq layer indicator (hatched = Coq time)
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=model_colors[p], edgecolor='black', label=provider_names[p])
        for p in providers
    ]
    # Add Coq indicator with white hatching (like Output Tokens in reference figure)
    coq_patch = Patch(facecolor='gray', edgecolor='white', label='Coq', hatch='////')
    legend_elements.append(coq_patch)
    
    ax.legend(handles=legend_elements, loc='upper left', fontsize=9, 
             ncol=3, title='Model', title_fontsize=9, framealpha=0.9)
    
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    output_dir = Path(output_dir)
    output_file = output_dir / "figure_complexity_runtime_all.pdf"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.savefig(str(output_file).replace('.pdf', '.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Saved: {output_file}")


def generate_complexity_size_graph(results, output_dir="paper_figures"):
    """
    Generate single proof size graph with all data
    Structure: 2 use cases × 3 complexities × 4 models = 24 bars
    Grouped by: Use Case → Complexity → Model
    Each model gets its own color (consistent across all graphs)
    Note: Groq disabled due to rate limits, AV disabled (will test with SLM later)
    """
    import numpy as np
    
    use_cases = ["tax", "recommendation"]  # AV disabled - will test with SLM later
    use_case_names = {
        "tax": "Tax",
        # "av": "AV",  # DISABLED
        "recommendation": "Rec"
    }
    providers = ["openai", "claude", "gemini", "groq", "deepseek"]  # 5 models
    num_models = len(providers)
    provider_names = {
        "openai": "OAI", 
        "claude": "Cla", 
        "gemini": "Gem",
        "groq": "Grq",
        "deepseek": "DS"
    }
    complexity_order = ['easy', 'medium', 'hard']
    complexity_names = {"easy": "Easy", "medium": "Med", "hard": "Hard"}
    
    # Colors by model (matching paper figure style)
    model_colors = {
        'openai': '#2E8B57',    # Green (OAI)
        'claude': '#E67E22',    # Orange (Cla)
        'gemini': '#4169E1',    # Blue/Purple (Gem)
        'groq': '#000000',      # Black (Grq)
        'deepseek': '#87CEEB',  # Light Blue (DS)
    }
    
    # Group results
    data = {}
    for result in results:
        if not result["success"]:
            continue
            
        use_case = result.get("use_case_type", "unknown")
        if use_case not in use_cases:
            continue
            
        provider = result["provider"]
        if provider not in providers:
            continue
            
        complexity = result.get("complexity", "medium")
        
        key = (use_case, complexity, provider)
        if key not in data:
            data[key] = []
        data[key].append(result["proof_size_lines"])
    
    # Calculate sizes and positions
    sizes = []
    colors = []
    x_positions = []
    
    bar_width = 0.5
    model_spacing = 0.1
    complexity_spacing = 1.2
    usecase_spacing = 2.5
    
    current_x = 0
    for i, use_case in enumerate(use_cases):
        if i > 0:
            current_x += usecase_spacing
        
        for j, complexity in enumerate(complexity_order):
            if j > 0:
                current_x += complexity_spacing
            
            for k, provider in enumerate(providers):
                if k > 0:
                    current_x += model_spacing
                
                key = (use_case, complexity, provider)
                if key in data and data[key]:
                    mean_size = statistics.mean(data[key])
                else:
                    mean_size = 0
                
                sizes.append(mean_size)
                colors.append(model_colors[provider])
                x_positions.append(current_x)
                current_x += bar_width
    
    # Create figure
    fig, ax = plt.subplots(figsize=(7, 4.5))
    
    bars = ax.bar(x_positions, sizes, width=bar_width, 
                  color=colors, edgecolor='black', linewidth=0.3)
    
    # Add value labels
    max_size = max(sizes) if sizes else 1
    for bar, size in zip(bars, sizes):
        if size > max_size * 0.05:
            ax.text(bar.get_x() + bar.get_width()/2., size,
                   f'{size:.0f}',
                   ha='center', va='bottom', fontsize=7)
    
    ax.set_ylabel('Proof Size (LOC)', fontsize=13, fontweight='bold')
    ax.set_ylim([0, max_size * 1.08])
    
    # X-axis: Complexity labels (calculate from actual x_positions)
    complexity_centers = []
    idx = 0
    for i, use_case in enumerate(use_cases):
        for j, complexity in enumerate(complexity_order):
            # Center of model bars for this complexity
            if idx + num_models - 1 < len(x_positions):
                center = (x_positions[idx] + x_positions[idx+num_models-1]) / 2
                complexity_centers.append(center)
            idx += num_models
    
    ax.set_xticks(complexity_centers)
    ax.set_xticklabels([complexity_names[c] for c in complexity_order] * len(use_cases), 
                       fontsize=9, rotation=0)
    
    # Add use case labels (no background)
    for i, use_case in enumerate(use_cases):
        start_idx = i * (3 * num_models)  # 3 complexities × num_models
        end_idx = start_idx + (3 * num_models) - 1
        if end_idx < len(x_positions):
            center = (x_positions[start_idx] + x_positions[end_idx]) / 2
            ax.text(center, -max_size * 0.12, use_case_names[use_case].upper(), 
                   ha='center', va='top', fontsize=11, fontweight='bold')
    
    # Add vertical separators between use cases (thick)
    for i in range(1, len(use_cases)):
        sep_idx = i*(3*num_models)
        if sep_idx < len(x_positions) and sep_idx > 0:
            sep_x = (x_positions[sep_idx - 1] + bar_width/2 + x_positions[sep_idx]) / 2
            ax.axvline(x=sep_x, color='black', linestyle='-', linewidth=1.5, alpha=0.7)
    
    # Add vertical separators between complexities (medium)
    for i in range(len(use_cases)):
        for j in range(1, len(complexity_order)):
            idx = i * (3 * num_models) + j * num_models
            if idx > 0 and idx < len(x_positions):
                sep_x = (x_positions[idx - 1] + bar_width/2 + x_positions[idx]) / 2
                ax.axvline(x=sep_x, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
    
    # Legend removed (not needed for paper figure)
    
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    output_dir = Path(output_dir)
    output_file = output_dir / "figure_complexity_size_all.pdf"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.savefig(str(output_file).replace('.pdf', '.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Saved: {output_file}")


def generate_complexity_token_graph(results, output_dir="paper_figures"):
    """
    Generate single token usage graph with all data
    Structure: 2 use cases × 3 complexities × 4 models = 24 bars
    Grouped by: Use Case → Complexity → Model
    Each model gets its own color (consistent across all graphs)
    Note: Groq disabled due to rate limits, AV disabled (will test with SLM later)
    """
    import numpy as np
    
    use_cases = ["tax", "recommendation"]  # AV disabled - will test with SLM later
    use_case_names = {
        "tax": "Tax",
        # "av": "AV",  # DISABLED
        "recommendation": "Rec"
    }
    providers = ["openai", "claude", "gemini", "groq", "deepseek"]  # 5 models
    num_models = len(providers)
    provider_names = {
        "openai": "OAI", 
        "claude": "Cla", 
        "gemini": "Gem",
        "groq": "Grq",
        "deepseek": "DS"
    }
    complexity_order = ['easy', 'medium', 'hard']
    complexity_names = {"easy": "Easy", "medium": "Med", "hard": "Hard"}
    
    # Colors by model (matching paper figure style)
    model_colors = {
        'openai': '#2E8B57',    # Green (OAI)
        'claude': '#E67E22',    # Orange (Cla)
        'gemini': '#4169E1',    # Blue/Purple (Gem)
        'groq': '#000000',      # Black (Grq)
        'deepseek': '#87CEEB',  # Light Blue (DS)
    }
    
    # Group results
    data = {}
    for result in results:
        if not result["success"]:
            continue
            
        use_case = result.get("use_case_type", "unknown")
        if use_case not in use_cases:
            continue
            
        provider = result["provider"]
        if provider not in providers:
            continue
            
        complexity = result.get("complexity", "medium")
        
        key = (use_case, complexity, provider)
        if key not in data:
            data[key] = []
        # Use SUCCESS-ONLY tokens to avoid outliers from retries
        data[key].append(result.get("success_tokens", result["total_tokens"]))
    
    # Calculate tokens and positions
    tokens = []
    colors = []
    x_positions = []
    
    bar_width = 0.5
    model_spacing = 0.1
    complexity_spacing = 1.2
    usecase_spacing = 2.5
    
    current_x = 0
    for i, use_case in enumerate(use_cases):
        if i > 0:
            current_x += usecase_spacing
        
        for j, complexity in enumerate(complexity_order):
            if j > 0:
                current_x += complexity_spacing
            
            for k, provider in enumerate(providers):
                if k > 0:
                    current_x += model_spacing
                
                key = (use_case, complexity, provider)
                if key in data and data[key]:
                    mean_tokens = statistics.mean(data[key])
                else:
                    mean_tokens = 0
                
                tokens.append(mean_tokens)
                colors.append(model_colors[provider])
                x_positions.append(current_x)
                current_x += bar_width
    
    # Create figure
    fig, ax = plt.subplots(figsize=(7, 4.5))
    
    bars = ax.bar(x_positions, tokens, width=bar_width, 
                  color=colors, edgecolor='black', linewidth=0.3)
    
    # Add value labels
    max_tokens = max(tokens) if tokens else 1
    for bar, token_count in zip(bars, tokens):
        if token_count > max_tokens * 0.05:
            if token_count >= 1000:
                label = f'{token_count/1000:.1f}K'
            else:
                label = f'{int(token_count)}'
            ax.text(bar.get_x() + bar.get_width()/2., token_count,
                   label,
                   ha='center', va='bottom', fontsize=7)
    
    ax.set_ylabel('Total Tokens', fontsize=13, fontweight='bold')
    ax.set_ylim([0, max_tokens * 1.08])
    
    # X-axis: Complexity labels (calculate from actual x_positions)
    complexity_centers = []
    idx = 0
    for i, use_case in enumerate(use_cases):
        for j, complexity in enumerate(complexity_order):
            # Center of model bars for this complexity
            if idx + num_models - 1 < len(x_positions):
                center = (x_positions[idx] + x_positions[idx+num_models-1]) / 2
                complexity_centers.append(center)
            idx += num_models
    
    ax.set_xticks(complexity_centers)
    ax.set_xticklabels([complexity_names[c] for c in complexity_order] * len(use_cases), 
                       fontsize=9, rotation=0)
    
    # Add use case labels (no background)
    for i, use_case in enumerate(use_cases):
        start_idx = i * (3 * num_models)  # 3 complexities × num_models
        end_idx = start_idx + (3 * num_models) - 1
        if end_idx < len(x_positions):
            center = (x_positions[start_idx] + x_positions[end_idx]) / 2
            ax.text(center, -max_tokens * 0.12, use_case_names[use_case].upper(), 
                   ha='center', va='top', fontsize=11, fontweight='bold')
    
    # Add vertical separators between use cases (thick)
    for i in range(1, len(use_cases)):
        sep_idx = i*(3*num_models)
        if sep_idx < len(x_positions) and sep_idx > 0:
            sep_x = (x_positions[sep_idx - 1] + bar_width/2 + x_positions[sep_idx]) / 2
            ax.axvline(x=sep_x, color='black', linestyle='-', linewidth=1.5, alpha=0.7)
    
    # Add vertical separators between complexities (medium)
    for i in range(len(use_cases)):
        for j in range(1, len(complexity_order)):
            idx = i * (3 * num_models) + j * num_models
            if idx > 0 and idx < len(x_positions):
                sep_x = (x_positions[idx - 1] + bar_width/2 + x_positions[idx]) / 2
                ax.axvline(x=sep_x, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
    
    # Legend removed (not needed for paper figure)
    
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    output_dir = Path(output_dir)
    output_file = output_dir / "figure_complexity_tokens_all.pdf"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.savefig(str(output_file).replace('.pdf', '.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Saved: {output_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate publication-quality graphs from PCO benchmark results")
    parser.add_argument("results_file", help="Path to benchmark results JSON file")
    parser.add_argument("-o", "--output-dir", default="paper_figures", help="Output directory for figures")
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 70)
    print("Generating Paper Figures")
    print("=" * 70)
    print()
    
    # Load results
    results = load_results(args.results_file)
    print(f"Loaded {len(results)} results from {args.results_file}")
    
    # Check if multiple providers
    providers = set(r["provider"] for r in results)
    print(f"Providers: {', '.join(providers)}")
    
    # Check if complexity data is present
    has_complexity = any("complexity" in r for r in results)
    print(f"Complexity data: {'Yes' if has_complexity else 'No'}")
    print()
    
    # Generate 4 core figures (all with 4 LLMs per use case)
    print("Generating 4 core graphs:\n")
    
    print("1. Output Size (Lines of Code)")
    generate_proof_size_graph(results, str(output_dir / "figure_1_output_size.pdf"))
    
    print("2. Runtime (LLM + Coq stacked)")
    generate_paper_graph_timing(results, str(output_dir / "figure_2_runtime.pdf"))
    
    print("3. Success Rate")
    generate_paper_graph_success_rate(results, str(output_dir / "figure_3_success_rate.pdf"))
    
    print("4. Token Count (Usage Efficiency)")
    generate_token_count_graph(results, str(output_dir / "figure_4_token_count.pdf"))
    
    # Generate RAG analysis graphs if tracking data is available
    has_rag_data = any("stage_first_attempt_time" in r for r in results)
    has_source = any("source" in r for r in results)
    
    if has_rag_data:
        print("\n" + "="*50)
        print("RAG Analysis Graphs")
        print("="*50)
        
        print("\n5. RAG Time Breakdown (time per stage per model)")
        generate_rag_time_breakdown_graph(results, output_dir)
        
        print("\n6. RAG Token Breakdown (tokens per stage per model)")
        generate_rag_tokens_breakdown_graph(results, output_dir)
        
        print("\n7. Average Time (successful attempts only)")
        generate_average_time_graph(results, output_dir)
        
        print("\n8. RAG Wasted Resources (success vs wasted)")
        generate_rag_wasted_graph(results, output_dir)
    
    if has_source:
        print("\n9. RAG Stage Distribution (which stage achieved success)")
        generate_rag_usage_graph(results, output_dir)
    
    # Generate complexity graphs if data is available
    if has_complexity:
        print("\nGenerating complexity analysis graphs (all-in-one format):\n")
        
        print("5. Success Rate vs Complexity (30 bars: 2 use cases × 3 complexities × 5 models)")
        generate_complexity_success_graph(results, str(output_dir))
        
        print("6. Runtime vs Complexity (30 bars: 2 use cases × 3 complexities × 5 models)")
        generate_complexity_runtime_graph(results, str(output_dir))
        
        print("7. Proof Size vs Complexity (30 bars: 2 use cases × 3 complexities × 5 models)")
        generate_complexity_size_graph(results, str(output_dir))
        
        print("8. Token Usage vs Complexity (30 bars: 2 use cases × 3 complexities × 5 models)")
        generate_complexity_token_graph(results, str(output_dir))
    
    # Generate tables
    print("\nGenerating tables:")
    generate_comparison_table(results, str(output_dir / "table_comparison.tex"))
    generate_size_table(results, str(output_dir / "table_proof_sizes.tex"))
    
    # Generate summary
    generate_paper_summary(results, str(output_dir / "paper_summary.txt"))
    
    print()
    print("=" * 70)
    if has_complexity:
        print("✓ All graphs generated successfully! (4 core + 4 complexity graphs)")
    else:
        print("✓ All 4 core graphs generated successfully!")
    print("=" * 70)
    print()
    print(f"Output directory: {output_dir}")
    print()
    print("Core graphs:")
    print("  1. figure_1_output_size.pdf/png      - Proof sizes (LOC)")
    print("  2. figure_2_runtime.pdf/png          - LLM + Coq timing (stacked)")
    print("  3. figure_3_success_rate.pdf/png     - Success rates (%)")
    print("  4. figure_4_token_count.pdf/png      - Token usage (efficiency)")
    print("  5. figure_rag_usage.pdf/png          - RAG stage distribution per model")
    print()
    
    if has_complexity:
        print("Complexity graphs (30 bars each: 2 use cases × 3 complexities × 5 models):")
        print("  Grouped by: Use Case → Complexity → Model")
        print("  Model colors: Blue (OpenAI), Green (Claude), Orange (Gemini), Purple (Groq), Red (DeepSeek)")
        print()
        print("  - figure_complexity_success_all.pdf/png  - Success rates by complexity")
        print("  - figure_complexity_runtime_all.pdf/png  - Runtime by complexity")
        print("  - figure_complexity_size_all.pdf/png     - Proof size by complexity")
        print("  - figure_complexity_tokens_all.pdf/png   - Token usage by complexity")
        print()
        print("  Structure per graph:")
        print("    [TAX: Easy(5 models) Med(5 models) Hard(5 models)]")
        print("    [AV:  Easy(5 models) Med(5 models) Hard(5 models)]")
        print("    [REC: Easy(5 models) Med(5 models) Hard(5 models)]")
        print()
    
    print("Tables and summary:")
    print("  - table_comparison.tex - LaTeX table: performance by use case")
    print("  - table_proof_sizes.tex - LaTeX table: proof sizes by use case & model")
    print("  - paper_summary.txt - Text summary with suggested paper text")
    print()
    print("To use in LaTeX paper:")
    print("  \\input{paper_figures/table_comparison.tex}")
    print("  \\includegraphics[width=\\textwidth]{paper_figures/figure_complexity_success_all.pdf}")
    print("  \\includegraphics[width=\\textwidth]{paper_figures/figure_complexity_runtime_all.pdf}")

def generate_rag_time_breakdown_graph(results, output_dir):
    """
    Generate graph showing TIME spent at each RAG stage per model BY WORKLOAD and COMPLEXITY.
    Format: Use Case × Complexity × Provider with stacked RAG stages.
    """
    print("\n" + "="*60)
    print("Generating RAG Time Breakdown Graph (by workload + complexity)")
    print("="*60)
    
    # RAG stages
    stages = ['stage_first_attempt_time', 'stage_error_rag_time', 
              'stage_final_rag_time']
    stage_labels = ['None', 'Error', 'Full']
    stage_colors = ['#2E8B57', '#FFD700', '#FFA500']
    
    provider_names = {
        'openai': 'OAI', 'claude': 'Cla', 'gemini': 'Gem',
        'groq': 'Grq', 'deepseek': 'DS'
    }
    
    # Use cases (workloads) and complexities
    use_cases = ["tax", "recommendation"]
    use_case_labels = {"tax": "TAX", "recommendation": "RECOMMENDATION"}
    complexities = ["easy", "medium", "hard"]
    complexity_labels = {"easy": "Easy", "medium": "Med", "hard": "Hard"}
    
    # Get providers
    providers = []
    for r in results:
        p = r.get('provider', '')
        if p and p not in providers:
            providers.append(p)
    
    # Calculate average time per stage per (use_case, complexity, provider)
    stage_times = {}
    for uc in use_cases:
        for comp in complexities:
            for p in providers:
                key = (uc, comp, p)
                stage_times[key] = {s: [] for s in stages}
    
    for r in results:
        provider = r.get('provider', '')
        use_case = r.get('use_case_type', r.get('use_case', ''))
        complexity = r.get('complexity', 'medium')
        
        # Map use_case to our categories
        if 'tax' in use_case.lower():
            uc = 'tax'
        elif 'recommendation' in use_case.lower():
            uc = 'recommendation'
        else:
            continue
        
        if not provider or provider not in providers:
            continue
        if complexity not in complexities:
            continue
        
        key = (uc, complexity, provider)
        for stage in stages:
            time_val = r.get(stage, 0)
            if time_val > 0:
                stage_times[key][stage].append(time_val)
    
    # Calculate averages
    avg_times = {}
    for key in stage_times:
        avg_times[key] = {}
        for stage in stages:
            times = stage_times[key][stage]
            avg_times[key][stage] = sum(times) / len(times) if times else 0
    
    # Create grouped bar chart: Use Case × Complexity × Provider
    # Same size as figure_complexity_runtime_all.pdf
    fig, ax = plt.subplots(figsize=(7, 4.5))
    
    num_providers = len(providers)
    num_complexities = len(complexities)
    num_usecases = len(use_cases)
    bar_width = 0.5  # Match complexity_runtime_graph
    
    # Build bar positions and data (matching complexity_runtime_graph spacing)
    model_spacing = 0.1
    complexity_spacing = 1.2
    usecase_spacing = 2.5
    
    x_positions = []
    all_heights = {stage: [] for stage in stages}
    
    current_x = 0
    usecase_centers = []
    complexity_centers = []
    
    for uc_idx, uc in enumerate(use_cases):
        if uc_idx > 0:
            current_x += usecase_spacing
        uc_start = current_x
        
        for comp_idx, comp in enumerate(complexities):
            if comp_idx > 0:
                current_x += complexity_spacing
            comp_start = current_x
            
            for p_idx, provider in enumerate(providers):
                if p_idx > 0:
                    current_x += model_spacing
                
                x_positions.append(current_x)
                key = (uc, comp, provider)
                
                for stage in stages:
                    all_heights[stage].append(avg_times.get(key, {}).get(stage, 0))
                
                current_x += bar_width
            
            complexity_centers.append((comp_start + current_x) / 2)
        
        usecase_centers.append((uc_start + current_x) / 2)
    
    # Plot stacked bars
    bottom = [0] * len(x_positions)
    
    for stage, label, color in zip(stages, stage_labels, stage_colors):
        heights = all_heights[stage]
        ax.bar(x_positions, heights, bar_width, bottom=bottom,
               label=label, color=color, edgecolor='black', linewidth=0.5)
        
        bottom = [b + h for b, h in zip(bottom, heights)]
    
    # Calculate max height for label positioning
    max_height = max(sum(all_heights[s][i] for s in stages) for i in range(len(x_positions))) if x_positions else 1
    
    # X-axis: complexity labels (matching complexity_runtime_graph style)
    complexity_centers_final = []
    idx = 0
    for uc in use_cases:
        for comp in complexities:
            center = (x_positions[idx] + x_positions[idx + num_providers - 1]) / 2
            complexity_centers_final.append(center)
            idx += num_providers
    
    ax.set_xticks(complexity_centers_final)
    ax.set_xticklabels([complexity_labels[c] for c in complexities] * num_usecases, 
                       fontsize=9, rotation=0)
    
    # Add use case labels below (matching style)
    for i, uc in enumerate(use_cases):
        start_idx = i * (3 * num_providers)
        end_idx = start_idx + (3 * num_providers) - 1
        if end_idx < len(x_positions):
            center = (x_positions[start_idx] + x_positions[end_idx]) / 2
            ax.text(center, -max_height * 0.12, use_case_labels[uc],
                   ha='center', va='top', fontsize=11, fontweight='bold')
    
    # Add vertical separators between use cases (thick)
    bars_per_usecase = num_complexities * num_providers
    if num_usecases > 1:
        sep_idx = bars_per_usecase
        if sep_idx < len(x_positions) and sep_idx > 0:
            sep_x = (x_positions[sep_idx - 1] + bar_width/2 + x_positions[sep_idx]) / 2
            ax.axvline(x=sep_x, color='black', linestyle='-', linewidth=1.5, alpha=0.7)
    
    # Add vertical separators between complexities (medium)
    for i in range(num_usecases):
        for j in range(1, num_complexities):
            idx = i * bars_per_usecase + j * num_providers
            if idx > 0 and idx < len(x_positions):
                sep_x = (x_positions[idx - 1] + bar_width/2 + x_positions[idx]) / 2
                ax.axvline(x=sep_x, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
    
    ax.set_ylabel('Time (seconds)', fontweight='bold', fontsize=11)
    
    # Legend ON the graph (matching style)
    ax.legend(title='RAG Stage', loc='upper right', fontsize=8, framealpha=0.9)
    ax.yaxis.grid(True, linestyle='--', alpha=0.3, linewidth=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    for fmt in ['png', 'pdf']:
        filepath = output_dir / f'figure_rag_time_breakdown.{fmt}'
        plt.savefig(filepath, dpi=300, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
    
    plt.close()
    print(f"✓ Saved: figure_rag_time_breakdown.png/pdf")


def generate_rag_tokens_breakdown_graph(results, output_dir):
    """
    Generate graph showing TOKENS spent at each RAG stage per model.
    Legend on graph, no title.
    """
    print("\n" + "="*60)
    print("Generating RAG Tokens Breakdown Graph")
    print("="*60)
    
    # RAG stages (Minimal Adapt removed - not used in final system)
    stages = ['stage_first_attempt_tokens', 'stage_error_rag_tokens', 
              'stage_final_rag_tokens']
    stage_labels = ['None', 'Error', 'Full']
    stage_colors = ['#2E8B57', '#FFD700', '#FFA500']
    
    provider_names = {
        'openai': 'OAI', 'claude': 'Cla', 'gemini': 'Gem',
        'groq': 'Grq', 'deepseek': 'DS'
    }
    
    providers = []
    for r in results:
        p = r.get('provider', '')
        if p and p not in providers:
            providers.append(p)
    
    # Calculate average tokens per stage per provider
    stage_tokens = {p: {s: [] for s in stages} for p in providers}
    
    for r in results:
        provider = r.get('provider', '')
        if not provider or provider not in providers:
            continue
        for stage in stages:
            tokens = r.get(stage, 0)
            if tokens > 0:
                stage_tokens[provider][stage].append(tokens)
    
    avg_tokens = {p: {} for p in providers}
    for p in providers:
        for stage in stages:
            tokens = stage_tokens[p][stage]
            avg_tokens[p][stage] = sum(tokens) / len(tokens) if tokens else 0
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = range(len(providers))
    bar_width = 0.6
    bottom = [0] * len(providers)
    
    for i, (stage, label, color) in enumerate(zip(stages, stage_labels, stage_colors)):
        heights = [avg_tokens[p][stage] for p in providers]
        
        bars = ax.bar(x, heights, bar_width, bottom=bottom, 
                     label=label, color=color, edgecolor='black', linewidth=0.5)
        
        for j, (h, b) in enumerate(zip(heights, bottom)):
            if h > 100:
                ax.text(j, b + h/2, f'{h:.0f}', ha='center', va='center', 
                       fontsize=8, fontweight='bold', color='black')
        
        bottom = [b + h for b, h in zip(bottom, heights)]
    
    for i, p in enumerate(providers):
        total = sum(avg_tokens[p][s] for s in stages)
        ax.text(i, total + 50, f'{total:.0f}', ha='center', va='bottom',
               fontsize=10, fontweight='bold')
    
    ax.set_ylabel('Average Tokens', fontweight='bold', fontsize=12)
    ax.set_xlabel('LLM Provider', fontweight='bold', fontsize=12)
    # No title - will be added in paper figure caption
    ax.set_xticks(x)
    ax.set_xticklabels([provider_names.get(p, p) for p in providers], fontsize=11)
    
    # Legend ON the graph (upper right inside)
    ax.legend(title='RAG Stage', loc='upper right', fontsize=9, framealpha=0.9)
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    
    for fmt in ['png', 'pdf']:
        filepath = output_dir / f'figure_rag_tokens_breakdown.{fmt}'
        plt.savefig(filepath, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
    
    plt.close()
    print(f"✓ Saved: figure_rag_tokens_breakdown.png/pdf")


def generate_average_time_graph(results, output_dir):
    """
    Generate graph showing AVERAGE TIME (successful attempts only) per model.
    Simple bar chart - one bar per provider.
    No title - will be added in paper figure caption.
    """
    print("\n" + "="*60)
    print("Generating Average Time Graph")
    print("="*60)
    
    provider_names = {
        'openai': 'OAI', 'claude': 'Cla', 'gemini': 'Gem',
        'groq': 'Grq', 'deepseek': 'DS'
    }
    
    # Provider colors (matching paper figure style)
    provider_colors = {
        'openai': '#2E8B57',      # Green (OAI)
        'claude': '#E67E22',      # Orange (Cla)
        'gemini': '#4169E1',      # Blue/Purple (Gem)
        'groq': '#000000',        # Black (Grq)
        'deepseek': '#87CEEB',    # Light Blue (DS)
    }
    
    providers = []
    for r in results:
        p = r.get('provider', '')
        if p and p not in providers:
            providers.append(p)
    
    # Calculate success time only
    success_time = {p: [] for p in providers}
    
    for r in results:
        provider = r.get('provider', '')
        if not provider or provider not in providers:
            continue
        # Use success_llm_time (only the successful attempt, no retries)
        success_time[provider].append(r.get('success_llm_time', r.get('llm_time', 0)))
    
    # Calculate averages
    avg_success_time = {p: sum(success_time[p])/len(success_time[p]) if success_time[p] else 0 for p in providers}
    
    # Create simple bar chart
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = range(len(providers))
    bar_width = 0.6
    
    colors = [provider_colors.get(p, '#888888') for p in providers]
    success_heights = [avg_success_time[p] for p in providers]
    
    bars = ax.bar(x, success_heights, bar_width, color=colors, edgecolor='black')
    
    ax.set_ylabel('Time (seconds)', fontweight='bold', fontsize=12)
    ax.set_xlabel('LLM Provider', fontweight='bold', fontsize=12)
    # No title - will be added in paper figure caption
    ax.set_xticks(x)
    ax.set_xticklabels([provider_names.get(p, p) for p in providers], fontsize=11)
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)
    
    # Add values on top of bars
    for i, h in enumerate(success_heights):
        ax.text(i, h + 0.2, f'{h:.1f}s', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    
    for fmt in ['png', 'pdf']:
        filepath = output_dir / f'figure_average_time.{fmt}'
        plt.savefig(filepath, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
    
    plt.close()
    print(f"✓ Saved: figure_average_time.png/pdf")


def generate_rag_wasted_graph(results, output_dir):
    """
    Generate graph showing SUCCESS vs WASTED time per model.
    Stacked bar chart - green (success) + red (wasted).
    No title - will be added in paper figure caption.
    """
    print("\n" + "="*60)
    print("Generating RAG Success vs Wasted Graph")
    print("="*60)
    
    provider_names = {
        'openai': 'OAI', 'claude': 'Cla', 'gemini': 'Gem',
        'groq': 'Grq', 'deepseek': 'DS'
    }
    
    providers = []
    for r in results:
        p = r.get('provider', '')
        if p and p not in providers:
            providers.append(p)
    
    # Calculate wasted vs success metrics
    wasted_time = {p: [] for p in providers}
    success_time = {p: [] for p in providers}
    
    for r in results:
        provider = r.get('provider', '')
        if not provider or provider not in providers:
            continue
        
        wasted_time[provider].append(r.get('wasted_llm_time', 0))
        success_time[provider].append(r.get('success_llm_time', 0))
    
    # Calculate averages
    avg_wasted_time = {p: sum(wasted_time[p])/len(wasted_time[p]) if wasted_time[p] else 0 for p in providers}
    avg_success_time = {p: sum(success_time[p])/len(success_time[p]) if success_time[p] else 0 for p in providers}
    
    # Create SINGLE stacked bar chart
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = range(len(providers))
    bar_width = 0.6
    
    # Stacked bars: success (bottom) + wasted (top)
    success_heights = [avg_success_time[p] for p in providers]
    wasted_heights = [avg_wasted_time[p] for p in providers]
    
    bars1 = ax.bar(x, success_heights, bar_width, 
                   label='Successful Attempt', color='#2E8B57', edgecolor='black')
    bars2 = ax.bar(x, wasted_heights, bar_width, bottom=success_heights,
                   label='Wasted on Errors', color='#FF6347', edgecolor='black')
    
    ax.set_ylabel('Time (seconds)', fontweight='bold', fontsize=12)
    ax.set_xlabel('LLM Provider', fontweight='bold', fontsize=12)
    # No title - will be added in paper figure caption
    ax.set_xticks(x)
    ax.set_xticklabels([provider_names.get(p, p) for p in providers], fontsize=11)
    ax.legend(fontsize=10, loc='upper right')
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)
    
    # Add values on stacked bars
    for i, (s, w) in enumerate(zip(success_heights, wasted_heights)):
        # Success value in middle of green bar
        if s > 0.5:
            ax.text(i, s/2, f'{s:.1f}s', ha='center', va='center', fontsize=9, fontweight='bold')
        # Wasted value in middle of red bar
        if w > 0.5:
            ax.text(i, s + w/2, f'{w:.1f}s', ha='center', va='center', fontsize=9, fontweight='bold')
        # Total on top
        total = s + w
        ax.text(i, total + 0.3, f'{total:.1f}s', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.tight_layout()
    
    for fmt in ['png', 'pdf']:
        filepath = output_dir / f'figure_rag_wasted.{fmt}'
        plt.savefig(filepath, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
    
    plt.close()
    print(f"✓ Saved: figure_rag_wasted.png/pdf")


def generate_rag_usage_graph(results, output_dir):
    """
    Generate graph showing RAG usage distribution per model.
    Shows which RAG stage each model needed to succeed.
    
    RAG Stages:
    - "llm": First attempt succeeded (Example + Rule RAG)
    - "llm_retry_N": Needed N Error RAG corrections  
    - "llm_rag_final": Needed Final RAG attempt
    - "llm_minimal_adapt": Needed Minimal Adaptation
    - "failed": All RAG stages failed
    """
    print("\n" + "="*60)
    print("Generating RAG Usage Graph")
    print("="*60)
    
    # Define RAG stages for display
    rag_stages = {
        'first_attempt': 'First Attempt\n(Example+Rule RAG)',
        'retry_1_2': 'Error RAG\n(1-2 retries)',
        'retry_3_plus': 'Error RAG\n(3+ retries)',
        'final_rag': 'Final RAG\nAttempt',
        'minimal_adapt': 'Minimal\nAdaptation',
    }
    
    # Colors for each RAG stage (gradient from green to red)
    stage_colors = {
        'first_attempt': '#2E8B57',   # Green - best
        'retry_1_2': '#90EE90',       # Light green
        'retry_3_plus': '#FFD700',    # Gold/Yellow
        'final_rag': '#FFA500',       # Orange
        'minimal_adapt': '#FF6347',   # Tomato - most help needed
    }
    
    # Provider display names
    provider_names = {
        'openai': 'OAI',
        'claude': 'Cla', 
        'gemini': 'Gem',
        'groq': 'Grq',
        'deepseek': 'DS'
    }
    
    # Get providers from results
    providers = []
    for r in results:
        p = r.get('provider', '')
        if p and p not in providers:
            providers.append(p)
    
    # Count RAG stage usage per provider
    stage_counts = {p: {s: 0 for s in rag_stages.keys()} for p in providers}
    total_counts = {p: 0 for p in providers}
    
    for r in results:
        provider = r.get('provider', '')
        if not provider or provider not in providers:
            continue
            
        source = r.get('source', 'failed')
        total_counts[provider] += 1
        
        # Categorize the source into RAG stages
        if source == 'llm':
            stage_counts[provider]['first_attempt'] += 1
        elif source in ['llm_retry_1', 'llm_retry_2']:
            stage_counts[provider]['retry_1_2'] += 1
        elif source.startswith('llm_retry_'):
            stage_counts[provider]['retry_3_plus'] += 1
        elif source == 'llm_rag_final':
            stage_counts[provider]['final_rag'] += 1
        elif source == 'llm_minimal_adapt':
            stage_counts[provider]['minimal_adapt'] += 1
        else:
            # Count failed as needing most help (or separate category)
            pass
    
    # Convert to percentages
    stage_pcts = {p: {} for p in providers}
    for p in providers:
        total = total_counts[p] if total_counts[p] > 0 else 1
        for s in rag_stages.keys():
            stage_pcts[p][s] = (stage_counts[p][s] / total) * 100
    
    # Create stacked bar chart
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = range(len(providers))
    bar_width = 0.6
    
    # Plot stacked bars
    bottom = [0] * len(providers)
    
    for stage_key, stage_label in rag_stages.items():
        heights = [stage_pcts[p][stage_key] for p in providers]
        color = stage_colors[stage_key]
        
        bars = ax.bar(x, heights, bar_width, bottom=bottom, 
                     label=stage_label, color=color, edgecolor='black', linewidth=0.5)
        
        # Add percentage labels on bars if > 5%
        for i, (h, b) in enumerate(zip(heights, bottom)):
            if h > 5:
                ax.text(i, b + h/2, f'{h:.0f}%', ha='center', va='center', 
                       fontsize=9, fontweight='bold', color='black')
        
        bottom = [b + h for b, h in zip(bottom, heights)]
    
    # Customize
    ax.set_ylabel('Percentage of Tests (%)', fontweight='bold', fontsize=12)
    ax.set_xlabel('LLM Provider', fontweight='bold', fontsize=12)
    ax.set_title('RAG Usage Distribution by Model\n(Which RAG stage achieved success)', 
                 fontweight='bold', fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels([provider_names.get(p, p) for p in providers], fontsize=11)
    ax.set_ylim(0, 105)
    
    # Legend outside
    ax.legend(title='RAG Stage', loc='upper left', bbox_to_anchor=(1.02, 1), fontsize=9)
    
    # Add grid
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)
    
    plt.tight_layout()
    
    # Save
    for fmt in ['png', 'pdf']:
        filepath = output_dir / f'figure_rag_usage.{fmt}'
        plt.savefig(filepath, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
    
    plt.close()
    print(f"✓ Saved: figure_rag_usage.png/pdf")
    
    # Print summary
    print("\nRAG Usage Summary:")
    print("-" * 60)
    for p in providers:
        print(f"\n{provider_names.get(p, p)}:")
        for s, label in rag_stages.items():
            pct = stage_pcts[p][s]
            if pct > 0:
                print(f"  {label.replace(chr(10), ' ')}: {pct:.1f}%")


if __name__ == '__main__':
    main()
