"""Verify every distributed input before reconstruction; never repair an input."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify() -> dict:
    manifest = json.loads((ROOT / "source_manifest.json").read_text(encoding="utf-8"))
    failures = []
    for item in manifest["files"]:
        path = (ROOT / item["path"]).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            failures.append(item["path"] + ": missing or unsafe path")
            continue
        raw = path.read_bytes()
        if len(raw) != item["bytes"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
            failures.append(item["path"] + ": checksum mismatch")
    if failures:
        raise RuntimeError("Source verification failed:\n" + "\n".join(failures))
    return {"status": "verified", "files": len(manifest["files"])}


if __name__ == "__main__":
    print(json.dumps(verify()))
