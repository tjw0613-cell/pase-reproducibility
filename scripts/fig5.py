"""Reconstruct Figure 5 from verified saved results."""
import argparse
import os
from pathlib import Path

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parents[1]/'outputs')
    args = parser.parse_args()
    os.environ['PASE_FIGURE_OUTPUT'] = str(args.output_dir.resolve())
    from _drawings import build
    build(5)
