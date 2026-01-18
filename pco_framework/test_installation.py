#!/usr/bin/env python3
"""
Test PCO Framework Installation
"""

import sys
from pathlib import Path


def check_python():
    """Check Python version"""
    if sys.version_info < (3, 7):
        return False, f"Python {sys.version_info.major}.{sys.version_info.minor} (need 3.7+)"
    return True, f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def check_module(module_name):
    """Check if Python module is installed"""
    try:
        __import__(module_name)
        return True, "Installed"
    except ImportError:
        return False, "Not installed"


def check_command(cmd):
    """Check if command is available"""
    import subprocess
    try:
        result = subprocess.run([cmd, "--version"], capture_output=True, timeout=5)
        return result.returncode == 0, "Available"
    except FileNotFoundError:
        return False, "Not found"
    except Exception as e:
        return False, str(e)


def main():
    print()
    print("=" * 70)
    print("PCO Framework - Installation Check")
    print("=" * 70)
    print()
    
    checks = []
    
    # Python version
    status, msg = check_python()
    checks.append(("Python 3.7+", status, msg))
    
    # Required modules
    checks.append(("tkinter", *check_module("tkinter")))
    
    # LLM modules (at least one needed)
    checks.append(("anthropic (Claude)", *check_module("anthropic")))
    checks.append(("openai", *check_module("openai")))
    
    # Optional but recommended
    checks.append(("coqc", *check_command("coqc")))
    checks.append(("rcoq", *check_command("rcoq")))
    
    # Storage directory
    storage_dir = Path("pco_storage")
    checks.append(("Storage dir", storage_dir.exists(), str(storage_dir)))
    
    # Print results
    print("Component                Status      Details")
    print("-" * 70)
    
    all_pass = True
    for component, status, details in checks:
        status_str = "✓ PASS" if status else "✗ FAIL"
        print(f"{component:20s} {status_str:12s} {details}")
        if not status and component in ["Python 3.7+", "tkinter"]:
            all_pass = False
    
    print()
    print("=" * 70)
    
    if all_pass:
        print("✅ Installation complete! Ready to use.")
        print()
        print("To start:")
        print("  python3 dashboard.py")
    else:
        print("⚠️  Some components missing:")
        print()
        has_anthropic = check_module("anthropic")[0]
        has_openai = check_module("openai")[0]
        if not has_anthropic and not has_openai:
            print("  pip install anthropic  # For Claude (recommended)")
            print("  # OR")
            print("  pip install openai     # For OpenAI")
        if not check_command("coqc")[0]:
            print("  brew install coq")
    
    print()


if __name__ == "__main__":
    main()
