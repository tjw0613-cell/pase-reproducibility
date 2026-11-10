#!/usr/bin/env python3
"""Regenerate the eight current figure presentations without rerunning analyses.

Figures 2–6 and S1 compose frozen, independently checked Origin panel PDFs.
Figure 1 redraws fixed schematic coordinates. Figure S2 plots the saved final
rejection-rate/Wilson table. None of these routes refits raw RNA/count data.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
ALL = ['fig1','fig2','fig3','fig4','fig5','fig6','figs1','figs2']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checked_source(base, relative):
    """Resolve only paths within the intended packaged source directory."""
    if not isinstance(relative, str) or not relative:
        raise ValueError('A source path must be a nonempty relative string')
    path = Path(relative.replace('\\','/'))
    if path.is_absolute() or PureWindowsPath(relative).drive or '..' in path.parts:
        raise ValueError(f'Unsafe source path: {relative}')
    resolved = (base/path).resolve()
    if not resolved.is_relative_to(base.resolve()):
        raise ValueError(f'Source path escapes its directory: {relative}')
    return resolved


def verify():
    manifest = json.loads((ROOT/'FILES.sha256.json').read_text(encoding='utf-8'))
    failures = []
    for item in manifest['files']:
        p = checked_source(ROOT,item['path'])
        if not p.is_file() or p.stat().st_size != item['bytes'] or sha(p) != item['sha256']:
            failures.append(item['path'])
    plans = sorted((ROOT/'plans').glob('*.json'))
    for path in plans:
        plan = json.loads(path.read_text(encoding='utf-8'))
        if sha(checked_source(ROOT/'inputs',plan['source_file'])) != plan['source_sha256']:
            failures.append('plan data: '+path.name)
        for item in plan.get('support_sources', []):
            if sha(checked_source(ROOT/'inputs',item['file'])) != item['sha256']:
                failures.append('plan support: '+item['file'])
    if len(plans) != 33:
        failures.append('expected 33 Origin panel plans')
    if failures:
        raise ValueError('Source verification failed: '+', '.join(failures))
    return {'status':'PASS','verified_files':len(manifest['files']), 'origin_panel_plans':len(plans),
            'file_manifest_sha256':sha(ROOT/'FILES.sha256.json')}


def render_one(key, output_dir, verification):
    import fitz
    from PIL import Image
    spec = json.loads((ROOT/'FIGURE_MANIFEST.json').read_text(encoding='utf-8'))['figures'][key]
    if key == 'fig1':
        cmd = [sys.executable, str(ROOT/'code/plot_figure1.py')]
    elif key == 'figs2':
        cmd = [sys.executable, str(ROOT/'code/plot_s2.py')]
    elif key in ['fig2','fig5','fig6']:
        cmd = [sys.executable, str(ROOT/'code/compose_2_5_6.py'), '--figures', key[3:]]
    else:
        cmd = [sys.executable, str(ROOT/'code/compose_3_4_s1.py'), '--figures', key[3:].upper()]
    env = os.environ.copy()
    env['PASE_FIGURE_OUTPUT_DIR'] = str(output_dir)
    env['PYTHONUTF8'] = '1'
    subprocess.run(cmd, check=True, env=env, cwd=output_dir)
    artifacts = {}
    for ext in ['pdf','svg','png','tiff']:
        p = output_dir/(spec['name']+'.'+ext)
        if not p.is_file():
            raise ValueError(f'Missing output {p}')
        artifacts[ext] = {'file':p.name,'sha256':sha(p),'bytes':p.stat().st_size}
    with fitz.open(output_dir/(spec['name']+'.pdf')) as pdf:
        if len(pdf) != 1:
            raise ValueError('Figure must have one PDF page')
        width, height = [v*25.4/72 for v in pdf[0].rect[2:]]
        if abs(width-spec['width_mm'])>.01 or abs(height-spec['height_mm'])>.01:
            raise ValueError(f'Wrong figure dimensions: {width} x {height}')
        if pdf[0].get_images():
            raise ValueError('Unexpected raster image in vector PDF')
    for ext in ['png','tiff']:
        with Image.open(output_dir/(spec['name']+'.'+ext)) as im:
            nominal = spec[ext+'_dpi']
            for pixels,mm in zip(im.size,[width,height]):
                if abs(pixels - mm/25.4*nominal)>1.2:
                    raise ValueError(f'{ext} raster dimensions inconsistent with {nominal} dpi')
            artifacts[ext]['pixels'] = list(im.size)
            artifacts[ext]['nominal_dpi'] = nominal
    sys.path.insert(0,str(ROOT/'code'))
    from font_policy import resolve_fonts
    receipt = {'created_utc':datetime.now(timezone.utc).isoformat(),'figure':key,'status':'PASS',
               'scope':spec['render_scope'],'source_verification':verification,
               'dimensions_mm':[width,height],'vector_pdf_rasters':0,
               'font_policy':resolve_fonts(),'artifacts':artifacts,
               'new_analysis_performed':False,'raw_count_reproduction_claimed':False,
               'visual_inspection':'not performed by this command'}
    (output_dir/(spec['name']+'_render_receipt.json')).write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'figure':key,'status':'PASS','scope':spec['render_scope'],'output_dir':str(output_dir)}))
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--figure',choices=['all']+ALL,default='all')
    parser.add_argument('--output-dir',type=Path,default=ROOT.parent/'outputs')
    parser.add_argument('--verify-only',action='store_true',help='Check packaged source hashes and all panel/data bindings without importing plotting libraries.')
    args = parser.parse_args()
    try:
        checked = verify()
        if args.verify_only:
            print(json.dumps(checked)); return 0
        output_dir = args.output_dir.resolve()
        if output_dir in [ROOT,ROOT.parent] or ROOT in output_dir.parents:
            raise ValueError('Choose a dedicated output directory outside current_figures; neither the repository root nor checked source directory can be an output directory.')
        output_dir.mkdir(parents=True,exist_ok=True)
        selected = ALL if args.figure=='all' else [args.figure]
        for key in selected:
            render_one(key,output_dir,checked)
        return 0
    except (OSError,ValueError,RuntimeError,subprocess.CalledProcessError) as exc:
        print(f'FIGURE_RENDER_FAILED: {exc}',file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
