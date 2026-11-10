"""Check current figure construction from a relocated repository copy."""
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

import fitz
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def run(arguments, cwd):
    result = subprocess.run([sys.executable, '-B', *map(str, arguments)], cwd=cwd,
                            capture_output=True, text=True, encoding='utf-8')
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return {'arguments': list(map(str, arguments)), 'exit_code': result.returncode,
            'stdout': result.stdout.strip(), 'stderr': result.stderr.strip()}


def main():
    report = {
        'checked_utc': datetime.now(timezone.utc).isoformat(),
        'system': platform.system(), 'python': platform.python_version(),
        'dependencies': {n: version(n) for n in ['numpy', 'pandas', 'matplotlib', 'Pillow', 'PyMuPDF']},
        'scope': 'Current figure construction, source integrity and frozen RNA summary checks; no new raw-data fit or formal simulation.',
        'manuscript_revision': '2026-11-09',
    }
    with tempfile.TemporaryDirectory(prefix='pase_current_check_') as temporary:
        temporary = Path(temporary).resolve()
        assert temporary.parent == Path(tempfile.gettempdir()).resolve()
        assert temporary.name.startswith('pase_current_check_')
        destination = temporary / 'portable project with spaces'
        shutil.copytree(ROOT, destination, ignore=shutil.ignore_patterns(
            'outputs', 'downloads', '__pycache__', '.git', '.venv', 'verification_report.json'))
        records = [run([destination / 'reproduce.py', 'verify'], temporary)]
        records.append(run(['-m', 'unittest', 'discover', '-s', 'tests', '-v'], destination))
        records.append(run([destination / 'reproduce.py', 'all'], temporary))
        records.append(run(['workflows/rna/signature/verify_signature.py'], destination))
        records.append(run(['workflows/rna/synthesis/pool.py', '--cohorts',
                            'data/biology/cohort_estimates.tsv', '--out', 'outputs/pool_check'], destination))
        records.append(run(['workflows/rna/compare_results.py', '--analysis', 'data/biology',
                            '--pooled', 'outputs/pool_check'], destination))
        records.append(run([destination / 'reproduce.py', 'verify'], temporary))
        for record in records:
            record['arguments'] = [v.replace(str(destination), 'RELOCATED_REPOSITORY') for v in record['arguments']]
            for key in ['stdout', 'stderr']:
                record[key] = record[key].replace(str(destination).replace('\\', '\\\\'), 'RELOCATED_REPOSITORY').replace(str(destination), 'RELOCATED_REPOSITORY')
        report['commands'] = records
        specs = json.loads((destination / 'current_figures/FIGURE_MANIFEST.json').read_text(encoding='utf-8'))['figures']
        pdfs = sorted((destination / 'outputs').glob('Figure_*.pdf'))
        expected_names = {s['name'] + '.pdf' for s in specs.values()}
        if {p.name for p in pdfs} != expected_names or len(pdfs) != 8:
            raise RuntimeError('Expected exactly the eight current figure PDFs.')
        report['figures'] = []
        for key, spec in specs.items():
            path = destination / 'outputs' / (spec['name'] + '.pdf')
            with fitz.open(path) as document:
                if len(document) != 1 or document[0].get_images():
                    raise RuntimeError('Expected a one-page vector PDF: ' + path.name)
                dimensions = [v * 25.4 / 72 for v in document[0].rect[2:]]
                if any(abs(a-b) > .01 for a,b in zip(dimensions, [spec['width_mm'], spec['height_mm']])):
                    raise RuntimeError('Incorrect PDF dimensions: ' + path.name)
            files = []
            for ext in ['pdf', 'svg', 'png', 'tiff']:
                output = path.with_suffix('.' + ext)
                record = {'file': output.name, 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'bytes': output.stat().st_size}
                if ext in ['png', 'tiff']:
                    with Image.open(output) as im:
                        dpi = spec[ext + '_dpi']
                        if any(abs(p - mm / 25.4 * dpi) > 1.2 for p,mm in zip(im.size, dimensions)):
                            raise RuntimeError('Incorrect raster dimensions: ' + output.name)
                        record['pixels'] = list(im.size)
                files.append(record)
            report['figures'].append({'figure': key, 'dimensions_mm': dimensions, 'scope': spec['render_scope'], 'files': files})
    report['status'] = 'passed'
    report['not_performed'] = ['fresh raw RNA fitting', 'new simulated cohorts', 'new external-method benchmark', 'Origin data-panel re-export']
    (ROOT / 'verification_report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('PASS: all eight current figures built in a relocated directory; source, tampering and RNA summary checks passed.')


if __name__ == '__main__':
    main()
