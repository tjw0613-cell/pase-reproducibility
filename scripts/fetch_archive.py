"""Download one published PASE archive and check its recorded size and SHA-256.

No archive is downloaded without a named selection. Files are not extracted,
and an existing file is never replaced. Use --verify-only for browser downloads.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CHUNK = 1024 * 1024


def catalogue() -> dict:
    return json.loads((ROOT / "archives.json").read_text(encoding="utf-8"))


def check_spec(spec: dict) -> None:
    name = spec["filename"]
    if not isinstance(name, str) or not name or name in (".", "..") or any(c in name for c in "/\\:"):
        raise ValueError("The archive filename must be a plain filename.")
    digest = spec["sha256"]
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("Invalid archive SHA-256.")
    if not isinstance(spec["bytes"], int) or spec["bytes"] <= 0:
        raise ValueError("Invalid archive size.")


def verify(path: Path, spec: dict) -> dict:
    check_spec(spec)
    if path.is_symlink():
        raise ValueError("Refusing a symbolic-link destination: " + str(path))
    if not path.is_file():
        raise FileNotFoundError("Archive not found: " + str(path))
    size = path.stat().st_size
    if size != spec["bytes"]:
        raise ValueError(f"Size mismatch for {path.name}: expected {spec['bytes']}, found {size}; file left unchanged.")
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK), b""):
            h.update(chunk)
    if h.hexdigest() != spec["sha256"]:
        raise ValueError(f"SHA-256 mismatch for {path.name}; file left unchanged.")
    return {"filename": path.name, "bytes": size, "sha256": h.hexdigest(), "status": "verified"}


def fetch(spec: dict, dest: Path, *, verify_only: bool = False, timeout: float = 60) -> dict:
    check_spec(spec)
    dest = dest.expanduser().resolve()
    final = dest / spec["filename"]
    if final.exists() or final.is_symlink() or verify_only:
        return verify(final, spec)
    dest.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        request = Request(spec["url"], headers={"User-Agent": "PASE-reproducibility/2026-11-10"})
        with urlopen(request, timeout=timeout) as response:
            # Temporary file and final destination share a filesystem. Only this
            # newly created temporary file is cleaned up on a download failure.
            with tempfile.NamedTemporaryFile(prefix=".pase-download-", suffix=".part", dir=dest, delete=False) as stream:
                temporary = Path(stream.name)
                size = 0
                while chunk := response.read(CHUNK):
                    size += len(chunk)
                    if size > spec["bytes"]:
                        raise ValueError("Download exceeds the recorded archive size.")
                    stream.write(chunk)
        verify(temporary, spec)
        # Exclusive creation prevents a concurrent download or a user file from
        # being overwritten between the first existence check and installation.
        try:
            with final.open("xb") as stream:
                try:
                    with temporary.open("rb") as source:
                        shutil.copyfileobj(source, stream, CHUNK)
                except BaseException:
                    stream.close()
                    final.unlink()
                    raise
        except FileExistsError:
            return verify(final, spec)
        return verify(final, spec)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    data = catalogue()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", nargs="?", choices=sorted(data["archives"]))
    parser.add_argument("--list", action="store_true", help="List files and sizes without downloading anything.")
    parser.add_argument("--dest", type=Path, default=Path("downloads"), help="Download directory, or directory containing an existing browser download.")
    parser.add_argument("--verify-only", action="store_true", help="Verify the selected filename in --dest without a network request.")
    args = parser.parse_args()
    if args.list or args.archive is None:
        for key, item in data["archives"].items():
            print(f"{key:14s} {item['bytes']:>12,d} bytes  {item['filename']}")
        return 0
    try:
        result = fetch(data["archives"][args.archive], args.dest, verify_only=args.verify_only)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
