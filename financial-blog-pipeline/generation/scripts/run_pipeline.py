#!/usr/bin/env python3
import os
import sys

# Ensure local src is importable when running from repo
CURRENT_DIR = os.path.dirname(__file__)
GEN_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
SRC_DIR = os.path.join(GEN_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from generation_pipeline.cli import cli

if __name__ == "__main__":
    cli()
