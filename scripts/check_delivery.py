"""Test the packaged sources and regenerate figures from a relocated directory."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

from PIL import Image
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]


def run(command, cwd, expected=0):
    result = subprocess.run([sys.executable, "-B", *command], cwd=cwd,
                            capture_output=True, text=True, encoding="utf-8")
    if result.returncode != expected:
        raise RuntimeError(result.stdout + result.stderr)
    return {"arguments": command, "exit_code": result.returncode,
            "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}


def main():
    report = {"checked_utc": datetime.now(timezone.utc).isoformat(),
              "system": platform.system(), "python": platform.python_version(),
              "dependencies": {n:version(n) for n in
                               ("matplotlib", "numpy", "Pillow", "reportlab", "pypdfium2")},
              "scope": "Source checks and figure reconstruction in a relocated directory; no raw cohort extraction or formal count simulation.",
              "formal_figures_3_4": "not_available"}
    with tempfile.TemporaryDirectory(prefix="pase_repro_check_") as temporary:
        temporary = Path(temporary).resolve()
        # Limit the automatic cleanup to the newly allocated temporary directory.
        assert temporary.parent == Path(tempfile.gettempdir()).resolve()
        assert temporary.name.startswith("pase_repro_check_")
        destination = temporary / "portable project"
        shutil.copytree(ROOT, destination,
                        ignore=shutil.ignore_patterns("outputs", "__pycache__", ".git", ".venv"))
        records = []
        records.append(run([str(destination/"reproduce.py"), "verify"], temporary))
        records.append(run(["-m", "unittest", "discover", "-s", "tests", "-v"], destination))
        records.append(run([str(destination/"reproduce.py"), "all-ready"], temporary))
        for n in (3,4):
            records.append(run([str(destination/"reproduce.py"), f"fig{n}"], temporary, expected=2))
        records.append(run(["workflows/rna/signature/verify_signature.py"], destination))
        records.append(run(["workflows/rna/synthesis/pool.py", "--cohorts",
                            "data/biology/cohort_estimates.tsv", "--out", "outputs/pool_check"], destination))
        records.append(run(["workflows/rna/compare_results.py", "--analysis", "data/biology",
                            "--pooled", "outputs/pool_check"], destination))
        # Do not distribute machine-specific temporary directory paths in logs.
        for record in records:
            record["arguments"] = [value.replace(str(destination), "RELOCATED_REPOSITORY") for value in record["arguments"]]
            for key in ("stdout", "stderr"):
                record[key] = record[key].replace(str(destination).replace("\\", "\\\\"), "RELOCATED_REPOSITORY").replace(str(destination), "RELOCATED_REPOSITORY")
        report["commands"] = records
        report["figures"] = []
        pdfs = sorted((destination / "outputs").glob("Figure_*.pdf"))
        if len(pdfs) != 4:
            raise RuntimeError("Expected exactly four completed figure PDFs.")
        for path in pdfs:
            item = {"name": path.stem, "files": []}
            with pdfium.PdfDocument(path) as doc:
                if len(doc) != 1:
                    raise RuntimeError("Each figure must have exactly one PDF page.")
                item["pdf_points"] = list(doc[0].get_size())
                if abs(item["pdf_points"][0] - 468) > 1e-5:
                    raise RuntimeError("Figure PDF width differs from 6.5 inches.")
            for ext, dpi in (("png",300), ("tiff",600)):
                image_path = path.with_suffix("."+ext)
                with Image.open(image_path) as im:
                    if im.width != int(6.5*dpi):
                        raise RuntimeError("Unexpected raster width: "+str(image_path))
                    dimensions = list(im.size)
                    actual_dpi = [float(x) for x in im.info.get("dpi",[])]
                    if not actual_dpi or abs(actual_dpi[0]-dpi)>.1:
                        raise RuntimeError("Missing or wrong resolution tag.")
                digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
                original = ROOT / "outputs" / image_path.name
                same = original.is_file() and hashlib.sha256(original.read_bytes()).hexdigest()==digest
                if not same:
                    raise RuntimeError("Relocated raster differs from local checked output: "+image_path.name)
                item["files"].append({"name":image_path.name, "sha256":digest,
                                      "pixels":dimensions, "dpi":actual_dpi, "matches_local_raster":same})
            report["figures"].append(item)
    report["status"] = "passed"
    report["not_tested"] = ["Linux/macOS execution", "fresh full raw-cohort extraction and fitting",
                            "new external-method benchmarking", "formal unified negative-binomial simulation"]
    output = ROOT / "verification_report.json"
    output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Passed: relocated reconstruction of Figures 1/2/5/6, source and regression checks, signature verification, pooling comparison; Figures 3/4 fail with exit 2.")


if __name__ == "__main__":
    main()
