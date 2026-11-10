"""Compatibility entry point for current figs2 construction."""
from pathlib import Path
import subprocess
import sys

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    raise SystemExit(subprocess.call([
        sys.executable, '-B', str(root / 'current_figures' / 'render.py'),
        '--figure', 'figs2', *sys.argv[1:],
    ]))
