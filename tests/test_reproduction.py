"""Regression checks for source integrity and safe archive handling."""
from __future__ import annotations
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import shutil
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


class ReproductionTests(unittest.TestCase):
    def test_all_pinned_sources_and_frozen_analysis_sources(self):
        checker = module("checker", "scripts/verify_sources.py")
        self.assertEqual(checker.verify()["status"], "verified")
        directory = ROOT / "workflows/rna/analysis"
        lock = json.loads((directory / "analysis_lock.json").read_text())
        for name, expected in lock["files"].items():
            self.assertEqual(hashlib.sha256((directory / name).read_bytes()).hexdigest(), expected, name)

    def test_tamper_is_rejected(self):
        checker = module("checker", "scripts/verify_sources.py")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "input.tsv").write_bytes(b"changed")
            (root / "source_manifest.json").write_text(json.dumps({"files":[{
                "path":"input.tsv", "bytes":4, "sha256":hashlib.sha256(b"good").hexdigest()}]}))
            with patch.object(checker, "ROOT", root):
                with self.assertRaisesRegex(RuntimeError, "checksum mismatch"):
                    checker.verify()

    def test_noncanonical_root_keeps_checksum_and_boundary_checks(self):
        checker = module("checker", "scripts/verify_sources.py")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "nested").mkdir()
            (root / "input.tsv").write_bytes(b"good")
            manifest = {"files":[{"path":"input.tsv", "bytes":4,
                                   "sha256":hashlib.sha256(b"good").hexdigest()}]}
            (root / "source_manifest.json").write_text(json.dumps(manifest))
            with patch.object(checker, "ROOT", root / "nested" / ".."):
                self.assertEqual(checker.verify()["status"], "verified")
                # Use an equal-size change so this proves the hash is checked.
                (root / "input.tsv").write_bytes(b"evil")
                with self.assertRaisesRegex(RuntimeError, "checksum mismatch"):
                    checker.verify()
                manifest["files"][0]["path"] = "../outside.tsv"
                (root / "source_manifest.json").write_text(json.dumps(manifest))
                with self.assertRaisesRegex(RuntimeError, "unsafe path"):
                    checker.verify()

    def test_current_figure_source_tamper_is_rejected(self):
        renderer = module('current_renderer', 'current_figures/render.py')
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / 'current figures'
            shutil.copytree(ROOT / 'current_figures', destination)
            with patch.object(renderer, 'ROOT', destination):
                self.assertEqual(renderer.verify()['status'], 'PASS')
                manifest = json.loads((destination / 'FILES.sha256.json').read_text(encoding='utf-8'))
                item = next(x for x in manifest['files'] if x['path'].endswith('.pdf'))
                target = destination / item['path']
                data = target.read_bytes()
                target.write_bytes(bytes([data[0] ^ 1]) + data[1:])
                with self.assertRaisesRegex(ValueError, 'Source verification failed'):
                    renderer.verify()

    def test_archive_extraction_and_traversal_rejection(self):
        helper = module("preparer", "workflows/rna/prepare_inputs.py")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "analysis").mkdir()
            raw = b"verified synthetic test bytes"
            (root / "analysis/expected_raw_sha256.json").write_text(json.dumps({
                "test":{"member.tsv":hashlib.sha256(raw).hexdigest()}}))
            good = root / "good.tar"
            with tarfile.open(good, "w") as archive:
                item = tarfile.TarInfo("a/member.tsv")
                item.size = len(raw)
                archive.addfile(item, io.BytesIO(raw))
            with patch.object(helper, "HERE", root):
                self.assertEqual(helper.extract("test", good, root / "safe"), 1)
                self.assertEqual(helper.verify("test", root / "safe"), 1)
                self.assertEqual(helper.extract("test", good, root / "safe"), 1)
                bad = root / "bad.tar"
                with tarfile.open(bad, "w") as archive:
                    item = tarfile.TarInfo("../member.tsv")
                    item.size = len(raw)
                    archive.addfile(item, io.BytesIO(raw))
                with self.assertRaisesRegex(ValueError, "Unsafe"):
                    helper.extract("test", bad, root / "blocked")
                self.assertFalse((root / "member.tsv").exists())


if __name__ == "__main__":
    unittest.main()
