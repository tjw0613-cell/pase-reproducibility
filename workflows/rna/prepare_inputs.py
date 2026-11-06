"""Safely extract pinned GEO members or verify complete cohort input folders."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile

HERE = Path(__file__).resolve().parent


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify(cohort, directory):
    expected = json.loads((HERE / "analysis/expected_raw_sha256.json").read_text())[cohort]
    failures = [name for name, value in expected.items()
                if not (directory / name).is_file() or digest(directory / name) != value]
    if failures:
        raise ValueError("Missing or mismatched input files: " + ", ".join(failures))
    return len(expected)


def extract(cohort, archive, directory):
    expected = json.loads((HERE / "analysis/expected_raw_sha256.json").read_text())[cohort]
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    seen = set()
    with tarfile.open(archive, "r:*") as container:
        for member in container:
            name = PurePosixPath(member.name).name
            if name not in expected:
                continue
            if not member.isfile() or ".." in PurePosixPath(member.name).parts:
                raise ValueError("Unsafe selected archive member: " + member.name)
            if name in seen:
                raise ValueError("Duplicate selected filename: " + name)
            seen.add(name)
            dest = directory / name
            if dest.exists():
                if not dest.is_file() or digest(dest) != expected[name]:
                    raise FileExistsError("Conflicting existing path: " + str(dest))
                continue
            partial = directory / (name + ".partial")
            if partial.exists():
                raise FileExistsError("Inspect the prior partial download: " + str(partial))
            try:
                with container.extractfile(member) as src, partial.open("xb") as dst:
                    while chunk := src.read(1024 * 1024):
                        dst.write(chunk)
                if digest(partial) != expected[name]:
                    raise ValueError("Checksum mismatch for archived member: " + name)
                partial.rename(dest)
            except Exception:
                partial.unlink(missing_ok=True)
                raise
    if not seen:
        raise ValueError("Archive contains no expected input files.")
    return len(seen)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    sub = cli.add_subparsers(dest="action", required=True)
    a = sub.add_parser("extract")
    a.add_argument("cohort", choices=["GSE234933", "GSE181919", "GSE310797"])
    a.add_argument("archive", type=Path)
    a.add_argument("directory", type=Path)
    v = sub.add_parser("verify")
    v.add_argument("cohort", choices=["GSE234933", "GSE181919", "GSE310797"])
    v.add_argument("directory", type=Path)
    args = cli.parse_args()
    n = extract(args.cohort, args.archive, args.directory) if args.action == "extract" else verify(args.cohort, args.directory)
    print(json.dumps({"action": args.action, "cohort": args.cohort, "verified_files": n}))
