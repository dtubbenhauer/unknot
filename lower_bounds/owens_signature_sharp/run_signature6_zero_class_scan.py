#!/usr/bin/env python3
"""Compatibility wrapper for the historical signature-six scan filename."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
cmd = [
    sys.executable,
    str(HERE / "run_signature_sharp_zero_class_scan.py"),
    "--k", "3",
    "-o", str(HERE / "signature6_zero_class_results.csv"),
    "--summary", str(HERE / "signature6_zero_class_summary.json"),
    *sys.argv[1:],
]
raise SystemExit(subprocess.call(cmd))
