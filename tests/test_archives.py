"""Archive downloads must be verified and must not overwrite user files."""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("pase_archive_fetch", ROOT / "scripts/fetch_archive.py")
fetcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetcher)


def archive_spec(data=b"small synthetic archive"):
    return {"filename": "test.zip", "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "url": "https://example.invalid/test.zip"}


class ArchiveTests(unittest.TestCase):
    def test_catalogue_preserves_version_and_later_supplement_boundaries(self):
        data = fetcher.catalogue()
        self.assertEqual(data["results_doi"], "10.5281/zenodo.24015713")
        self.assertEqual(data["protocol_doi"], "10.5281/zenodo.24010816")
        self.assertEqual(len(data["archives"]), 5)
        for entry in data["archives"].values():
            fetcher.check_spec(entry)
            self.assertTrue(entry["url"].startswith("https://zenodo.org/records/24015713/files/"))
            self.assertTrue(entry["url"].endswith(entry["filename"] + "?download=1"))
        for entry in data["submission_supplements"].values():
            fetcher.check_spec(entry)
            self.assertNotIn("url", entry)
            self.assertIn("not in Zenodo record 24015713", entry["availability"])

    def test_successful_download_and_existing_match_need_no_second_request(self):
        data = b"small synthetic archive"
        record = archive_spec(data)
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory) / "path with spaces"
            with patch.object(fetcher, "urlopen", return_value=io.BytesIO(data)) as request:
                self.assertEqual(fetcher.fetch(record, dest)["status"], "verified")
                self.assertEqual(fetcher.fetch(record, dest)["status"], "verified")
                request.assert_called_once()
            self.assertEqual((dest / "test.zip").read_bytes(), data)
            self.assertEqual(list(dest.glob("*.part")), [])
            self.assertEqual(list(dest.glob(".pase-download-*")), [])

    def test_existing_different_file_is_never_replaced(self):
        record = archive_spec(b"good")
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory)
            path = dest / "test.zip"
            path.write_bytes(b"evil")  # Same size: this must exercise SHA-256.
            with patch.object(fetcher, "urlopen") as request:
                with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                    fetcher.fetch(record, dest)
                request.assert_not_called()
            self.assertEqual(path.read_bytes(), b"evil")

    def test_corrupt_or_oversized_download_is_not_installed(self):
        record = archive_spec(b"good")
        for data in (b"evil", b"go", b"too much"):
            with self.subTest(data=data), tempfile.TemporaryDirectory() as directory:
                dest = Path(directory)
                with patch.object(fetcher, "urlopen", return_value=io.BytesIO(data)):
                    with self.assertRaises(ValueError):
                        fetcher.fetch(record, dest)
                self.assertFalse((dest / "test.zip").exists())
                self.assertEqual(list(dest.iterdir()), [])

    def test_verify_only_never_downloads_or_creates_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory) / "missing"
            with patch.object(fetcher, "urlopen") as request:
                with self.assertRaises(FileNotFoundError):
                    fetcher.fetch(archive_spec(), dest, verify_only=True)
                request.assert_not_called()
            self.assertFalse(dest.exists())

    def test_unsafe_names_are_rejected_before_writing(self):
        for filename in ("../outside.zip", "..\\outside.zip", "C:test.zip", ".", ".."):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as directory:
                record = {**archive_spec(), "filename": filename}
                with self.assertRaisesRegex(ValueError, "plain filename"):
                    fetcher.fetch(record, Path(directory))
                self.assertEqual(list(Path(directory).iterdir()), [])

    def test_concurrent_creation_is_preserved_and_verified(self):
        data = b"good"
        record = archive_spec(data)
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory)

            def request(*args, **kwargs):
                # Simulate another process creating the file after our first
                # existence check, while our network download is starting.
                (dest / "test.zip").write_bytes(b"evil")
                return io.BytesIO(data)

            with patch.object(fetcher, "urlopen", side_effect=request):
                with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                    fetcher.fetch(record, dest)
            self.assertEqual((dest / "test.zip").read_bytes(), b"evil")
            self.assertEqual(list(dest.glob(".pase-download-*")), [])

    def test_no_selection_only_lists_packages(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, str(ROOT / "scripts/fetch_archive.py")],
                                    cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("2,938,313,334", result.stdout)
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
