#!/usr/bin/env python3
"""Run local protocol tests that require no TypeSafe API key."""
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
raise SystemExit(subprocess.call([sys.executable, "-m", "unittest", "discover", "-s", str(root / "tests"), "-v"]))
