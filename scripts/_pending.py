"""Refuse to draw inferential plots without completed registered simulations."""
import argparse
import json
from pathlib import Path
import sys


def main(figure: str) -> int:
    parser = argparse.ArgumentParser(description=f"Status of {figure}")
    parser.add_argument("--output-dir", type=Path)
    parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    status = json.loads((root / "figure_status.json").read_text(encoding="utf-8"))[figure]
    print(f"{figure.upper()}: NOT AVAILABLE. {status['reason']}", file=sys.stderr)
    print("No figure was created. See FORMAL_SIMULATION.md for the required evidence.", file=sys.stderr)
    return 2
