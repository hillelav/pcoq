#!/usr/bin/env python3
"""
Generate Publication-Quality Graphs for Temporal Logic Benchmark

Creates 4 graphs matching the style of static logic benchmarks:
1. Success Rate by Complexity
2. Runtime by Complexity (SLM + RTAMT stacked)
3. Spec Size by Complexity
4. Token Usage by Complexity (Input + Output stacked)

Use cases: turn, brake
Complexities: easy, medium
SLMs: llama, phi, qwen, codellama
"""

import json
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image, ImageDraw, ImageFont


def load_results(results_file):
    """Load benchmark results from JSON file"""
    with open(results_file, 'r') as f:
        return json.load(f)


def create_model_logo(model_name, color, size=100):
    """
    Create a simple circular logo with model initial/emoji
    
    Args:
        model_name: Model identifier (llama, phi, qwen, codellama)
        color: Hex color for the logo
        size: Size of the logo in pixels
    
    Returns:
        PIL Image object
    """
    # Model symbols (emoji or text)
    symbols = {
        "llama": "🦙",
        "phi": "Φ",
        "qwen": "通",
        "codellama": "</>",
    }
    
    # Create image with transparent background
    img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw circle background
    margin = 5
    circle_color = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    draw.ellipse([margin, margin, size-margin, size-margin], 
                 fill=circle_color + (220,), outline=(0, 0, 0, 255), width=2)
    
    # Add text/emoji
    symbol = symbols.get(model_name, model_name[0].upper())
    
    try:
        # Try to use a font that supports emoji
        font_size = size // 2
        try:
            # Try system fonts
            font = ImageFont.truetype("/System/Library/Fonts/Apple Color Emoji.ttc", font_size)
        except:
            try:
                font = ImageFont.truetype("Arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        # Get text bounding box
        bbox = draw.textbbox((0, 0), symbol, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center text
        x = (size - text_width) / 2 - bbox[0]
        y = (size - text_height) / 2 - bbox[1]
        
        # Draw text (white for visibility)
        draw.text((x, y), symbol, fill=(255, 255, 255, 255), font=font)
    except Exception as e:
        # Fallback: just draw the first letter
        draw.text((size//4, size//4), model_name[0].upper(), 
                 fill=(255, 255, 255, 255))
    
    return img


def get_or_create_logo(model_name, color):
    """
    Load logo from file or create it if it doesn't exist
    
    Args:
        model_name: Model identifier
        color: Hex color for the logo
    
    Returns:
        numpy array suitable for matplotlib
    """
    logos_dir = Path(__file__).parent / "model_logos"
    logo_path = logos_dir / f"{model_name}_logo.png"
    
    # Try to load existing logo
    if logo_path.exists():
        try:
            img = Image.open(logo_path)
            # Resize to standard size
            img = img.resize((100, 100), Image.Resampling.LANCZOS)
            return np.array(img)
        except Exception as e:
            print(f"Warning: Could not load {logo_path}: {e}")
    
    # Create logo if it doesn't exist
    img = create_model_logo(model_name, color, size=100)
    
    # Save for future use
    logos_dir.mkdir(exist_ok=True)
    try:
        img.save(logo_path)
        print(f"✓ Created logo: {logo_path}")
    except Exception as e:
        print(f"Warning: Could not save logo: {e}")
    
    return np.array(img)


def add_logos_to_graph(ax, x_positions, bar_providers, colors, y_max, bar_width):
    """
    Add small, professional model logos above the bars
    Uses PNG images if available, otherwise falls back to text symbols
    
    Args:
        ax: Matplotlib axis
        x_positions: X positions of bars
        bar_providers: List of provider names for each bar
        colors: List of colors for each bar  
        y_max: Maximum y value (for positioning)
        bar_width: Width of bars
    """
    # Text symbols as fallback
    symbols = {
        "openai": "⚡",
        "claude": "◐", 
        "gemini": "✦",  # Better Gemini star
        "groq": "◉",    # Circle for Groq
        "deepseek": "🐋", # Whale for DeepSeek
        "llama": "🦙",
        "phi": "Φ",
        "qwen": "通",
        "codellama": "</>",
    }
    
    # Find the first occurrence of each provider
    added_providers = set()
    logos_dir = Path(__file__).parent / "model_logos"
    
    for x_pos, provider, color in zip(x_positions, bar_providers, colors):
        if provider not in added_providers:
            # Try to use PNG logo first
            logo_path = logos_dir / f"{provider}_logo.png"
            
            if logo_path.exists():
                try:
                    # Use actual logo image
                    img = Image.open(logo_path)
                    img = img.resize((50, 50), Image.Resampling.LANCZOS)  # Small size
                    imagebox = OffsetImage(img, zoom=0.3)  # Small zoom
                    ab = AnnotationBbox(imagebox, (x_pos, y_max * 1.03),
                                      frameon=False, pad=0, box_alignment=(0.5, 0.5))
                    ax.add_artist(ab)
                    added_providers.add(provider)
                    continue
                except Exception as e:
                    print(f"Warning: Could not load {logo_path}, using text fallback")
            
            # Fallback to text symbol
            symbol = symbols.get(provider, provider[0].upper())
            ax.text(x_pos, y_max * 1.02, symbol,
                   fontsize=14,
                   ha='center', va='center',
                   color='white',
                   weight='bold',
                   bbox=dict(boxstyle='circle,pad=0.25', 
                           facecolor=color, 
                           edgecolor='black',
                           alpha=0.95,
                           linewidth=1.5))
            
            added_providers.add(provider)


def generate_complexity_success_graph(results, output_dir="paper_figures"):
    """
    Generate success rate graph by complexity
    Structure: 2 use cases × 3 complexities × 4 SLMs = 24 bars
    """
    use_cases = ["turn", "brake"]
    use_case_names = {"turn": "Turn", "brake": "Brake"}
    
    providers = ["llama", "phi", "qwen", "codellama"]
    provider_names = {
        "llama": "Llama", 
        "phi": "Phi", 
        "qwen": "Qwen",
        "codellama": "Code"
    }
    
    # SLM colors (distinct from LLM colors)
    model_colors = {
        "llama": "#FF6B6B",    # Coral red
        "phi": "#4ECDC4",      # Turquoise
        "qwen": "#95E1D3",     # Mint
        "codellama": "#F38181" # Light coral
    }
    
    complexity_order = ['easy', 'medium', 'hard']
    complexity_names = {"easy": "Easy", "medium": "Med", "hard": "Hard"}
    
    # Collect data
    data = {}
    for result in results:
        key = (result['use_case'], result['complexity'], result['provider'])
        if key not in data:
            data[key] = []
        data[key].append(result["success"])
    
    # Calculate success rates
    success_rates = []
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
            center = (x_positions[idx] + x_positions[idx+num_models-1]) / 2
            complexity_centers.append(center)
            idx += num_models
    
    ax.set_xticks(complexity_centers)
    ax.set_xticklabels([complexity_names[c] for c in complexity_order] * len(use_cases), 
                       fontsize=9, rotation=0)
    
    # Add use case labels
    for i, use_case in enumerate(use_cases):
        start_idx = i * (3 * num_models)
        center = (x_positions[start_idx] + x_positions[start_idx + (3 * num_models) - 1]) / 2
        ax.text(center, -12, use_case_names[use_case].upper(), 
               ha='center', va='top', fontsize=11, fontweight='bold')
    
    # Add vertical separators
    for i in range(1, len(use_cases)):
        sep_x = (x_positions[i*(3*num_models) - 1] + bar_width/2 + x_positions[i*(3*num_models)]) / 2
        ax.axvline(x=sep_x, color='black', linestyle='-', linewidth=1.5, alpha=0.7)
    
    for i in range(len(use_cases)):
        for j in range(1, len(complexity_order)):
            idx = i * (3 * num_models) + j * num_models
            if idx > 0 and idx < len(x_positions):
                sep_x = (x_positions[idx - 1] + bar_width/2 + x_positions[idx]) / 2
                ax.axvline(x=sep_x, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
    
    # Legend removed
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.axhline(y=100, color='gray', linestyle=':', linewidth=0.8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    output_dir = Path(output_dir)
    output_file = output_dir / "figure_temporal_success_all.pdf"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.savefig(str(output_file).replace('.pdf', '.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Saved: {output_file}")


def generate_complexity_runtime_graph(results, output_dir="paper_figures"):
    """
    Generate runtime graph by complexity (SLM + RTAMT stacked)
    """
    use_cases = ["turn", "brake"]
    use_case_names = {"turn": "Turn", "brake": "Brake"}
    
    providers = ["llama", "phi", "qwen", "codellama"]
    provider_names = {
        "llama": "Llama", 
        "phi": "Phi", 
        "qwen": "Qwen",
        "codellama": "Code"
    }
    
    model_colors = {
        "llama": "#FF6B6B",
        "phi": "#4ECDC4",
        "qwen": "#95E1D3",
        "codellama": "#F38181"
    }
    
    complexity_names = {"easy": "Easy", "medium": "Med", "hard": "Hard"}
    
    # Collect data (successful runs only)
    data = {}
    complexities_in_results = set()
    for result in results:
        if result['success']:
            key = (result['use_case'], result['complexity'], result['provider'])
            complexities_in_results.add(result['complexity'])
            if key not in data:
                data[key] = {'llm_times': [], 'verify_times': []}
            data[key]['llm_times'].append(result['llm_time'])
            data[key]['verify_times'].append(result['verification_time'])
    
    # Only include complexities that have successful results
    complexity_order = [c for c in ['easy', 'medium', 'hard'] if c in complexities_in_results]
    
    # Calculate averages and track structure for x-axis
    llm_times = []
    rtamt_times = []
    colors = []
    x_positions = []
    bar_providers = []  # Track which provider each bar belongs to
    complexity_positions = {}  # Track positions for each (use_case, complexity)
    
    bar_width = 0.5
    model_spacing = 0.1
    complexity_spacing = 1.2
    usecase_spacing = 2.5
    num_models = len(providers)
    
    current_x = 0
    for i, use_case in enumerate(use_cases):
        if i > 0:
            current_x += usecase_spacing
        
        for j, complexity in enumerate(complexity_order):
            if j > 0:
                current_x += complexity_spacing
            
            complexity_start_x = current_x
            
            for k, provider in enumerate(providers):
                if k > 0:
                    current_x += model_spacing
                
                key = (use_case, complexity, provider)
                # ONLY add bar if there is successful data (no empty bars for failures)
                if key in data and data[key]['llm_times']:
                    llm_avg = sum(data[key]['llm_times']) / len(data[key]['llm_times'])
                    rtamt_avg = sum(data[key]['verify_times']) / len(data[key]['verify_times'])
                    
                    llm_times.append(llm_avg)
                    rtamt_times.append(rtamt_avg)
                    colors.append(model_colors[provider])
                    x_positions.append(current_x)
                    bar_providers.append(provider)  # Track provider for this bar
                
                # Always advance position (maintains spacing even if bar skipped)
                current_x += bar_width
            
            # Record center of this complexity group
            complexity_positions[(use_case, complexity)] = (complexity_start_x + current_x - bar_width) / 2
    
    # Create figure with stacked bars
    fig, ax = plt.subplots(figsize=(7, 4.5))
    
    # Stack: SLM time (bottom) + RTAMT time (top, white hatching)
    bars_slm = ax.bar(x_positions, llm_times, width=bar_width, 
                      color=colors, edgecolor='black', linewidth=0.3)
    
    bars_rtamt = ax.bar(x_positions, rtamt_times, width=bar_width, bottom=llm_times,
                       color=colors, edgecolor='white', linewidth=0.5, 
                       hatch='////', zorder=3)
    
    for bar in bars_rtamt:
        bar.set_edgecolor('white')
    
    # Add total time labels
    max_runtime = max([l + r for l, r in zip(llm_times, rtamt_times)]) if llm_times else 1
    for x, llm_t, rtamt_t in zip(x_positions, llm_times, rtamt_times):
        total_t = llm_t + rtamt_t
        if total_t > max_runtime * 0.05:
            ax.text(x, total_t,
                   f'{total_t:.2f}',
                   ha='center', va='bottom', fontsize=7)
    
    ax.set_ylabel('Time (seconds)', fontsize=13, fontweight='bold')
    ax.set_ylim([0, max_runtime * 1.12])  # Small space for compact logos
    
    # X-axis labels using tracked positions
    complexity_centers = []
    complexity_labels = []
    for use_case in use_cases:
        for complexity in complexity_order:
            if (use_case, complexity) in complexity_positions:
                complexity_centers.append(complexity_positions[(use_case, complexity)])
                complexity_labels.append(complexity_names[complexity])
    
    ax.set_xticks(complexity_centers)
    ax.set_xticklabels(complexity_labels, fontsize=9, rotation=0)
    
    # Use case labels
    num_complexities = len(complexity_order)
    for i, use_case in enumerate(use_cases):
        start_idx = i * (num_complexities * num_models)
        end_idx = start_idx + (num_complexities * num_models) - 1
        if end_idx < len(x_positions):
            center = (x_positions[start_idx] + x_positions[end_idx]) / 2
            ax.text(center, -max_runtime * 0.12, use_case_names[use_case].upper(), 
                   ha='center', va='top', fontsize=11, fontweight='bold')
    
    # Separators
    for i in range(1, len(use_cases)):
        sep_idx = i*(num_complexities*num_models)
        if sep_idx < len(x_positions) and sep_idx > 0:
            sep_x = (x_positions[sep_idx - 1] + bar_width/2 + x_positions[sep_idx]) / 2
            ax.axvline(x=sep_x, color='black', linestyle='-', linewidth=1.5, alpha=0.7)
    
    for i in range(len(use_cases)):
        for j in range(1, num_complexities):
            idx = i * (num_complexities * num_models) + j * num_models
            if idx > 0 and idx < len(x_positions):
                sep_x = (x_positions[idx - 1] + bar_width/2 + x_positions[idx]) / 2
                ax.axvline(x=sep_x, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
    
    # Legend: SLMs + RTAMT indicator
    legend_elements = [
        mpatches.Patch(facecolor=model_colors[p], edgecolor='black', label=provider_names[p])
        for p in providers
    ]
    rtamt_patch = mpatches.Patch(facecolor='gray', edgecolor='white', label='RTAMT', hatch='////')
    legend_elements.append(rtamt_patch)
    
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9, 
             ncol=3, title='SLM', title_fontsize=9, framealpha=0.9)
    
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Apply tight_layout FIRST (before adding logos)
    plt.tight_layout()
    
    # Add model logos above bars (AFTER tight_layout so they don't get clipped)
    add_logos_to_graph(ax, x_positions, bar_providers, colors, max_runtime, bar_width)
    
    output_dir = Path(output_dir)
    output_file = output_dir / "figure_temporal_runtime_all.pdf"
    # Don't use bbox_inches='tight' - it clips the logos!
    plt.savefig(output_file, dpi=300)
    plt.savefig(str(output_file).replace('.pdf', '.png'), dpi=300)
    plt.close()
    print(f"  ✓ Saved: {output_file}")


def generate_complexity_size_graph(results, output_dir="paper_figures"):
    """
    Generate spec size graph by complexity
    """
    use_cases = ["turn", "brake"]
    use_case_names = {"turn": "Turn", "brake": "Brake"}
    
    providers = ["llama", "phi", "qwen", "codellama"]
    provider_names = {
        "llama": "Llama", 
        "phi": "Phi", 
        "qwen": "Qwen",
        "codellama": "Code"
    }
    
    model_colors = {
        "llama": "#FF6B6B",
        "phi": "#4ECDC4",
        "qwen": "#95E1D3",
        "codellama": "#F38181"
    }
    
    complexity_order = ['easy', 'medium', 'hard']
    complexity_names = {"easy": "Easy", "medium": "Med", "hard": "Hard"}
    
    # Collect data
    data = {}
    for result in results:
        if result['success']:
            key = (result['use_case'], result['complexity'], result['provider'])
            if key not in data:
                data[key] = []
            data[key].append(result['spec_length'])
    
    # Calculate averages
    sizes = []
    colors = []
    x_positions = []
    
    bar_width = 0.5
    model_spacing = 0.1
    complexity_spacing = 1.2
    usecase_spacing = 2.5
    num_models = len(providers)
    
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
                    avg_size = sum(data[key]) / len(data[key])
                else:
                    avg_size = 0
                
                sizes.append(avg_size)
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
    
    ax.set_ylabel('Spec Length (chars)', fontsize=13, fontweight='bold')
    ax.set_ylim([0, max_size * 1.08])
    
    # X-axis labels
    complexity_centers = []
    idx = 0
    for i, use_case in enumerate(use_cases):
        for j, complexity in enumerate(complexity_order):
            if idx + num_models - 1 < len(x_positions):
                center = (x_positions[idx] + x_positions[idx+num_models-1]) / 2
                complexity_centers.append(center)
            idx += num_models
    
    ax.set_xticks(complexity_centers)
    ax.set_xticklabels([complexity_names[c] for c in complexity_order] * len(use_cases), 
                       fontsize=9, rotation=0)
    
    # Use case labels
    for i, use_case in enumerate(use_cases):
        start_idx = i * (3 * num_models)
        end_idx = start_idx + (3 * num_models) - 1
        if end_idx < len(x_positions):
            center = (x_positions[start_idx] + x_positions[end_idx]) / 2
            ax.text(center, -max_size * 0.12, use_case_names[use_case].upper(), 
                   ha='center', va='top', fontsize=11, fontweight='bold')
    
    # Separators
    for i in range(1, len(use_cases)):
        sep_idx = i*(3*num_models)
        if sep_idx < len(x_positions) and sep_idx > 0:
            sep_x = (x_positions[sep_idx - 1] + bar_width/2 + x_positions[sep_idx]) / 2
            ax.axvline(x=sep_x, color='black', linestyle='-', linewidth=1.5, alpha=0.7)
    
    for i in range(len(use_cases)):
        for j in range(1, len(complexity_order)):
            idx = i * (3 * num_models) + j * num_models
            if idx > 0 and idx < len(x_positions):
                sep_x = (x_positions[idx - 1] + bar_width/2 + x_positions[idx]) / 2
                ax.axvline(x=sep_x, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
    
    # Legend removed
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    output_dir = Path(output_dir)
    output_file = output_dir / "figure_temporal_size_all.pdf"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.savefig(str(output_file).replace('.pdf', '.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Saved: {output_file}")


def generate_complexity_token_graph(results, output_dir="paper_figures"):
    """
    Generate token usage graph by complexity (Input + Output stacked)
    """
    use_cases = ["turn", "brake"]
    use_case_names = {"turn": "Turn", "brake": "Brake"}
    
    providers = ["llama", "phi", "qwen", "codellama"]
    provider_names = {
        "llama": "Llama", 
        "phi": "Phi", 
        "qwen": "Qwen",
        "codellama": "Code"
    }
    
    model_colors = {
        "llama": "#FF6B6B",
        "phi": "#4ECDC4",
        "qwen": "#95E1D3",
        "codellama": "#F38181"
    }
    
    complexity_order = ['easy', 'medium', 'hard']
    complexity_names = {"easy": "Easy", "medium": "Med", "hard": "Hard"}
    
    # Collect data
    data = {}
    for result in results:
        if result['success']:
            key = (result['use_case'], result['complexity'], result['provider'])
            if key not in data:
                data[key] = {'input': [], 'output': []}
            data[key]['input'].append(result['tokens_input'])
            data[key]['output'].append(result['tokens_output'])
    
    # Calculate averages
    input_tokens = []
    output_tokens = []
    colors = []
    x_positions = []
    
    bar_width = 0.5
    model_spacing = 0.1
    complexity_spacing = 1.2
    usecase_spacing = 2.5
    num_models = len(providers)
    
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
                if key in data and data[key]['input']:
                    input_avg = sum(data[key]['input']) / len(data[key]['input'])
                    output_avg = sum(data[key]['output']) / len(data[key]['output'])
                else:
                    input_avg = 0
                    output_avg = 0
                
                input_tokens.append(input_avg)
                output_tokens.append(output_avg)
                colors.append(model_colors[provider])
                x_positions.append(current_x)
                current_x += bar_width
    
    # Create figure with stacked bars
    fig, ax = plt.subplots(figsize=(7, 4.5))
    
    # Stack: Input (bottom) + Output (top, white hatching)
    bars_input = ax.bar(x_positions, input_tokens, width=bar_width, 
                        color=colors, edgecolor='black', linewidth=0.3)
    
    bars_output = ax.bar(x_positions, output_tokens, width=bar_width, bottom=input_tokens,
                         color=colors, edgecolor='white', linewidth=0.5, 
                         hatch='////', zorder=3)
    
    for bar in bars_output:
        bar.set_edgecolor('white')
    
    # Add total token labels
    max_tokens = max([i + o for i, o in zip(input_tokens, output_tokens)]) if input_tokens else 1
    for x, input_t, output_t in zip(x_positions, input_tokens, output_tokens):
        total_t = input_t + output_t
        if total_t > max_tokens * 0.05:
            if total_t >= 1000:
                label = f'{total_t/1000:.1f}K'
            else:
                label = f'{int(total_t)}'
            ax.text(x, total_t,
                   label,
                   ha='center', va='bottom', fontsize=7)
    
    ax.set_ylabel('Total Tokens', fontsize=13, fontweight='bold')
    ax.set_ylim([0, max_tokens * 1.08])
    
    # X-axis labels
    complexity_centers = []
    idx = 0
    for i, use_case in enumerate(use_cases):
        for j, complexity in enumerate(complexity_order):
            if idx + num_models - 1 < len(x_positions):
                center = (x_positions[idx] + x_positions[idx+num_models-1]) / 2
                complexity_centers.append(center)
            idx += num_models
    
    ax.set_xticks(complexity_centers)
    ax.set_xticklabels([complexity_names[c] for c in complexity_order] * len(use_cases), 
                       fontsize=9, rotation=0)
    
    # Use case labels
    for i, use_case in enumerate(use_cases):
        start_idx = i * (3 * num_models)
        end_idx = start_idx + (3 * num_models) - 1
        if end_idx < len(x_positions):
            center = (x_positions[start_idx] + x_positions[end_idx]) / 2
            ax.text(center, -max_tokens * 0.12, use_case_names[use_case].upper(), 
                   ha='center', va='top', fontsize=11, fontweight='bold')
    
    # Separators
    for i in range(1, len(use_cases)):
        sep_idx = i*(3*num_models)
        if sep_idx < len(x_positions) and sep_idx > 0:
            sep_x = (x_positions[sep_idx - 1] + bar_width/2 + x_positions[sep_idx]) / 2
            ax.axvline(x=sep_x, color='black', linestyle='-', linewidth=1.5, alpha=0.7)
    
    for i in range(len(use_cases)):
        for j in range(1, len(complexity_order)):
            idx = i * (3 * num_models) + j * num_models
            if idx > 0 and idx < len(x_positions):
                sep_x = (x_positions[idx - 1] + bar_width/2 + x_positions[idx]) / 2
                ax.axvline(x=sep_x, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
    
    # Legend removed
    ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    output_dir = Path(output_dir)
    output_file = output_dir / "figure_temporal_tokens_all.pdf"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.savefig(str(output_file).replace('.pdf', '.png'), dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Saved: {output_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate temporal logic graphs")
    parser.add_argument("results_file", help="Path to benchmark results JSON file")
    parser.add_argument("-o", "--output-dir", default="paper_figures", 
                       help="Output directory for figures")
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 70)
    print("Generating Temporal Logic Paper Figures")
    print("=" * 70)
    print()
    
    # Load results
    results = load_results(args.results_file)
    print(f"Loaded {len(results)} results from {args.results_file}")
    print()
    
    # Generate all graphs
    print("1. Success Rate by Complexity (24 bars: 2 use cases × 3 complexities × 4 SLMs)")
    generate_complexity_success_graph(results, str(output_dir))
    
    print("2. Runtime by Complexity (SLM + RTAMT stacked)")
    generate_complexity_runtime_graph(results, str(output_dir))
    
    print("3. Spec Size by Complexity")
    generate_complexity_size_graph(results, str(output_dir))
    
    print("4. Token Usage by Complexity (Input + Output stacked)")
    generate_complexity_token_graph(results, str(output_dir))
    
    print()
    print("=" * 70)
    print("✓ All figures generated successfully!")
    print("=" * 70)
    print()
    print("Output files:")
    print(f"  - {output_dir}/figure_temporal_success_all.pdf")
    print(f"  - {output_dir}/figure_temporal_runtime_all.pdf")
    print(f"  - {output_dir}/figure_temporal_size_all.pdf")
    print(f"  - {output_dir}/figure_temporal_tokens_all.pdf")


if __name__ == "__main__":
    main()
