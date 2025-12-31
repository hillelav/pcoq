#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent

EXTS = {".vo", ".vos", ".vok", ".glob"}

def main():
    removed = 0
    for p in ROOT.rglob("*"):
        if p.suffix in EXTS:
            p.unlink()
            removed += 1
    print(f"🧹 Cleaned {removed} generated Coq files")

if __name__ == "__main__":
    main()

