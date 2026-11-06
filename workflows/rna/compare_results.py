"""Compare refitted table fields with the archived Figure 2/6 inputs."""
import argparse
import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def compare(expected, actual):
    def read(path):
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream, delimiter="\t")
            return reader.fieldnames, list(reader)
    columns, a = read(expected)
    other, b = read(actual)
    if columns != other or len(a) != len(b):
        raise ValueError("Table dimensions differ: " + actual.name)
    for i, (row, reference) in enumerate(zip(b, a), 1):
        for key in columns:
            left, right = row[key], reference[key]
            if left == right:
                continue
            try:
                equal = math.isclose(float(left), float(right), rel_tol=1e-7, abs_tol=1e-9)
            except (ValueError, TypeError):
                equal = False
            if not equal:
                raise ValueError(f"Mismatch in {actual.name}, row {i}, {key}: {left} vs {right}")
    print(f"Verified {actual.name}: {len(a)} rows; numerical atol=1e-9, rtol=1e-7.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--pooled", type=Path, required=True)
    args = parser.parse_args()
    for name in ("cohort_estimates.tsv", "pooling_influence.tsv"):
        compare(ROOT / "data/biology" / name, args.analysis / name)
    compare(ROOT / "data/biology/pooled.tsv", args.pooled / "pooled.tsv")
