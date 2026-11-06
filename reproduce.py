"""Portable entry point for reconstruction of the PASE manuscript figures."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
READY = ("fig1", "fig2", "fig5", "fig6")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=[*(f"fig{i}" for i in range(1, 7)), "all-ready", "verify", "status"])
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs")
    args = parser.parse_args()
    if args.target == "verify":
        return subprocess.call([sys.executable, "-B", str(ROOT / "scripts" / "verify_sources.py")])
    if args.target == "status":
        print((ROOT / "figure_status.json").read_text(encoding="utf-8"))
        return 0
    targets = READY if args.target == "all-ready" else (args.target,)
    for target in targets:
        command = [sys.executable, "-B", str(ROOT / "scripts" / f"{target}.py"),
                   "--output-dir", str(args.output_dir.resolve())]
        result = subprocess.call(command)
        if result:
            return result
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
