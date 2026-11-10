"""Compose short-label Figures 3, 4 and S1 from verified Origin PDF panels.

All data marks, data labels, heatmap colours, error bars and curves are made in
Origin. This script places each panel at its native millimetre size and adds
only editable headings, axis labels, legends and shared colour scales.

Run only after the corresponding Origin evidence and PDF exports are complete:
    python compose_3_4_s1.py --figures 3 4 S1
"""
from pathlib import Path
import argparse
import json

import fitz

from compose_5_6 import (
    Composer, ROOT, OUT, PANELS, PLANS, MM, BLUE, VERM, GREY, BLACK,
    rgb, sha, spec,
)
from colour_contract import colour_contract


METHODS = ['equal_r_t', 'fixed_z_wald', 'dl_wald', 'dl_hk', 'reml_hk', 'reml_mkh']
METHOD_LABELS = [
    ('Equal-patient t',), ('Fixed Fisher–Wald',), ('DL–Wald',),
    ('DL–HKSJ',), ('REML–HKSJ',), ('REML–mHKSJ',),
]
HETEROGENEITY = ['τ = 0', 'τ = 0.1', 'τ = 0.2', 'Bimodal', '20% reversal']
COHORTS = ['GSE234933', 'GSE181919', 'GSE310797']
REQUIRED = {
    '3': ['F3A', 'F3B', 'F3C'],
    '4': ['F4' + letter for letter in 'ABCDEFGHI'],
    'S1': ['FS1_' + cohort for cohort in COHORTS],
}


def source_checks(ids, require_panels=True):
    checks = {}
    for panel_id in ids:
        plan_path = PLANS / (panel_id + '.json')
        if not plan_path.is_file():
            raise FileNotFoundError(f'Pending Origin plan: {plan_path}')
        plan = spec(panel_id)
        source = ROOT / 'inputs' / plan['source_file']
        if not source.is_file() or sha(source) != plan['source_sha256']:
            raise ValueError(f'{panel_id}: source hash does not match the Origin plan')
        if require_panels and not (PANELS / panel_id / 'result.pdf').is_file():
            raise FileNotFoundError(f'Pending Origin PDF: {panel_id}')
        checks[panel_id] = {
            'plan_sha256': sha(plan_path),
            'source_file': source.relative_to(ROOT).as_posix(),
            'source_sha256': sha(source),
        }
    return checks


def finish(name, composer, extra):
    receipt = composer.save()
    if receipt['checks']['embedded_rasters']:
        raise RuntimeError(f'{name}: unexpected raster inside the vector figure')
    receipt.update(extra)
    receipt.update({
        'composition_script_sha256': sha(Path(__file__)),
        'all_origin_panels_native_size': all(
            item['scale'] == 1 for item in receipt['panel_sources']),
        'assembled_editable_origin_project_claimed': False,
        'external_text_editable_in_svg': True,
        'no_new_statistical_quantities': True,
        'visual_QA': 'pending actual inspection of the composed PDF',
    })
    (OUT / (name + '_composition.json')).write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    return receipt


def vertical_text(composer, x, centre_y, text, size=7.5):
    length_mm = composer.font.text_length(text, fontsize=size) / MM
    composer.text(x, centre_y + length_mm / 2, text, size, rotate=90)


def colourbar(composer, source_plan, x, y, width=40, height=2.4):
    """Use the exact same colour contract as the Origin-native heatmap."""
    contract = colour_contract(source_plan)
    low, high = contract['zmin'], contract['zmax']
    for a, b, colour in zip(
            contract['levels'][:-1], contract['levels'][1:], contract['colours']):
        xa = x + width * (a - low) / (high - low)
        xb = x + width * (b - low) / (high - low)
        composer.page.draw_rect(
            fitz.Rect(xa * MM, y * MM, xb * MM, (y + height) * MM),
            color=rgb(colour), fill=rgb(colour), width=0)
    coverage = source_plan['mode'] == 'coverage'
    if coverage:
        points = [(x, y), (x - 1.6, y + height / 2), (x, y + height), (x, y)]
        colour, labels = contract['below_colour'], ['≤90', '95', '100']
    else:
        points = [(x + width, y), (x + width + 1.6, y + height / 2),
                  (x + width, y + height), (x + width, y)]
        colour, labels = contract['above_colour'], ['0', '5', '≥10']
    shape = composer.page.new_shape()
    shape.draw_polyline([fitz.Point(a * MM, b * MM) for a, b in points])
    shape.finish(color=rgb(colour), fill=rgb(colour), width=0)
    shape.commit()
    for xpos, label in zip([x, x + width / 2, x + width], labels):
        composer.text(xpos, y + height + 3.4, label, 7.1, align='center')
    return {'source_mode': source_plan['mode'], 'contract': contract,
            'x_mm': x, 'y_mm': y, 'width_mm': width, 'height_mm': height}


def heatmap_geometry(plan, left, top):
    g = plan['geometry_percent']
    return {
        'left': left + plan['width_mm'] * g['left'] / 100,
        'top': top + plan['height_mm'] * g['top'] / 100,
        'width': plan['width_mm'] * g['width'] / 100,
        'height': plan['height_mm'] * g['height'] / 100,
    }


def figure3():
    checks = source_checks(REQUIRED['3'])
    c = Composer('Figure_3', 188)
    lefts, top = [54, 96, 138], 14
    titles = [('A', 'Coverage (μ = 0)'), ('B', 'Coverage (μ = 0.1)'),
              ('C', 'Type I error')]
    expected_rows = [f'{method}_{i}' for method in METHODS for i in range(5)]
    boxes = []
    for panel_id, left, (letter, title) in zip(REQUIRED['3'], lefts, titles):
        p = spec(panel_id)
        if (p['width_mm'], p['height_mm']) != (40, 148):
            raise ValueError(f'{panel_id}: native-size heatmap contract changed')
        if p['rows'] != expected_rows or p['columns'] != ['4', '6', '8', '12', '20', '40']:
            raise ValueError(f'{panel_id}: method/heterogeneity/patient ordering changed')
        if p['geometry_percent'] != {'left': 1, 'top': 1, 'width': 98, 'height': 98}:
            raise ValueError(f'{panel_id}: native layer geometry changed')
        if p['palette'] != 'purple_teal' or p.get('show_row_labels', True) or p.get('show_column_labels', True):
            raise ValueError(f'{panel_id}: expected purple/teal and hidden native category labels')
        if len(p['values']) != 30 or any(len(row) != 6 for row in p['values']):
            raise ValueError(f'{panel_id}: expected 180 Origin-native labelled cells')
        c.text(left, 8, letter, 10, True, color='#000000')
        c.text(left + 5, 8, title, 7.25, True)
        c.place(panel_id, left, top)
        box = heatmap_geometry(p, left, top)
        boxes.append(box)
        for i, patients in enumerate(p['columns']):
            x = box['left'] + box['width'] * (i + .5) / 6
            c.text(x, box['top'] + box['height'] + 4, patients, 7.2, align='center')

    # Label each 5-row group once; values remain entirely inside Origin PDFs.
    box = boxes[0]
    row_h = box['height'] / 30
    c.text(1, 8, 'Method', 7.4, True)
    c.text(52.5, 8, 'Heterogeneity', 7.4, True, align='right')
    for group, method_lines in enumerate(METHOD_LABELS):
        start = box['top'] + group * 5 * row_h
        centre = start + 2.5 * row_h
        for line_no, line in enumerate(method_lines):
            y = centre + .85 + (line_no - (len(method_lines) - 1) / 2) * 3.5
            c.text(1, y, line, 7.2, True)
        # Gutter-only bracket; no external line overwrites data or annotations.
        c.line(29, start + .9, 29, start + 5 * row_h - .9, '#B3B9BF', .55)
        c.line(28, start + .9, 29, start + .9, '#B3B9BF', .55)
        c.line(28, start + 5 * row_h - .9, 29, start + 5 * row_h - .9, '#B3B9BF', .55)
        for row, label in enumerate(HETEROGENEITY):
            c.text(52.5, start + (row + .5) * row_h + .85, label, 7.0, align='right')
    c.text(116, 171, 'Patients (J)', 7.5, align='center')
    c.text(80, 177, 'Coverage (%)', 7.4, align='center')
    c.text(145, 177, 'Type I error (%)', 7.4, align='center')
    bars = [colourbar(c, spec('F3A'), 60, 179),
            colourbar(c, spec('F3C'), 125, 179)]
    return finish('Figure_3', c, {
        'source_verification': checks,
        'matrix_cells': 540,
        'data_annotation_origin': 'All 540 numerical annotations are native Origin labels.',
        'external_data_annotations': 0,
        'colourbars': bars,
        'colourbar_builder_sha256': sha(ROOT / 'code' / 'colour_contract.py'),
        'method_order': METHODS,
        'heterogeneity_order': HETEROGENEITY,
        'native_heatmap_boxes_mm': boxes,
        'scientific_changes': False,
    })


def method_legend(c, x, y, text, colour):
    c.line(x, y - .7, x + 5, y - .7, colour, .9)
    c.text(x + 7, y, text, 7.5)


def patient_legend(c, x, y, label, square=False):
    colour = '#555555'
    c.page.draw_line((x * MM, (y - .7) * MM), ((x + 7) * MM, (y - .7) * MM),
                     color=rgb(colour), width=.75,
                     dashes='[0.75 3.75] 0' if square else None)
    r = .7
    rectangle = fitz.Rect((x + 3.5 - r) * MM, (y - .7 - r) * MM,
                          (x + 3.5 + r) * MM, (y - .7 + r) * MM)
    if square:
        c.page.draw_rect(rectangle, color=rgb(colour), fill=(1, 1, 1), width=.75)
    else:
        c.page.draw_oval(rectangle, color=rgb(colour), fill=rgb(colour), width=.75)
    c.text(x + 9, y, label)


def figure4():
    checks = source_checks(REQUIRED['4'])
    c = Composer('Figure_4', 176)
    lefts, tops = [1, 82, 132], [22, 70, 118]
    method_legend(c, 8, 5, 'Equal-patient t', BLUE)
    method_legend(c, 59, 5, 'REML–HKSJ', VERM)
    patient_legend(c, 113, 5, 'J = 8')
    patient_legend(c, 147, 5, 'J = 20', square=True)
    headings = ['Cell yield', 'MMP14 gate', '15-gene gate']
    row_labels = [
        ['Bias', 'Δ target', 'Δ target'],
        ['RMSE', 'Δ bias', 'Δ bias'],
        ['CI width', 'Δ width', 'Δ width'],
    ]
    for col, title in enumerate(headings):
        p = spec('F4' + 'ABC'[col])
        centre = lefts[col] + p['width_mm'] * (p['layer_box'][0] + p['layer_box'][2] / 2) / 100
        c.text(centre, 15, title, 8, True, align='center')
    placed = {}
    for row in range(3):
        for col in range(3):
            letter = chr(ord('A') + row * 3 + col)
            panel_id = 'F4' + letter
            p = spec(panel_id)
            width = 78 if col == 0 else 47
            box = [20, 7, 75, 78] if col == 0 else [26, 7, 69, 78]
            if (p['width_mm'], p['height_mm']) != (width, 44) or p['layer_box'] != box:
                raise ValueError(f'{panel_id}: native-size or layer contract changed')
            for series in p['series']:
                label = series['label']
                colour = BLUE if label.startswith('equal_r_t') else VERM
                symbol = 1 if 'J=20' in label else 2
                if series['color'] != colour or series['symbol'] != symbol or series['dash'] != ('J=20' in label):
                    raise ValueError(f'{panel_id}: colour/shape/line contract changed')
            x, y = lefts[col], tops[row]
            c.text(x + 1, y, letter, 10, True, color='#000000')
            c.place(panel_id, x, y)
            centre_y = y + p['height_mm'] * (box[1] + box[3] / 2) / 100
            vertical_text(c, x + 2, centre_y, row_labels[row][col])
            placed[panel_id] = p

    # Five observed categories: balanced baseline plus four imbalance/coupling cases.
    categories = [('Equal',), ('Lognormal', 'uncoupled'), ('Lognormal', 'coupled'),
                  ('Dominant', 'uncoupled'), ('Dominant', 'coupled')]
    p = placed['F4G']
    if p.get('show_xlabels', True):
        raise ValueError('F4G numeric category ticks must be hidden in the Origin panel')
    bottom = tops[2] + p['height_mm'] * (p['layer_box'][1] + p['layer_box'][3]) / 100
    category_positions = []
    for i, lines in enumerate(categories):
        x = c.x_data(p, i, lefts[0])
        for j, label in enumerate(lines):
            c.text(x, bottom + 4 + j * 3.4, label, 7.0, align='center')
        category_positions.append({'source_position': i, 'label': ' '.join(lines), 'x_mm': x})
    c.text(46, 171, 'Cell allocation', 7.5, align='center')
    for col, panel_id in [(1, 'F4H'), (2, 'F4I')]:
        p = placed[panel_id]
        centre = lefts[col] + p['width_mm'] * (p['layer_box'][0] + p['layer_box'][2] / 2) / 100
        c.text(centre, 168, 'Latent μ', 7.5, align='center')
    return finish('Figure_4', c, {
        'source_verification': checks,
        'category_coordinate_labels': category_positions,
        'legend_contract': {'colour': {'equal_r_t': BLUE, 'reml_hk': VERM},
                            'patient_count': {'8': 'filled circle, solid line',
                                              '20': 'open square, dotted line'}},
        'scientific_changes': False,
    })


def figureS1():
    checks = source_checks(REQUIRED['S1'])
    c = Composer('Figure_S1', 73)
    colours = None
    for i, cohort in enumerate(COHORTS):
        left, top = 1 + i * 60, 9
        p = spec('FS1_' + cohort)
        if (p['width_mm'], p['height_mm']) != (57, 46):
            raise ValueError(f'FS1_{cohort}: native-size contract changed')
        ecdf = next(series for series in p['series'] if series.get('line_only'))
        anchor = next(series for series in p['series'] if series['label'] == 'LILRB4')
        this_colours = (ecdf['color'], anchor['color'])
        if colours is not None and colours != this_colours:
            raise ValueError('ECDF and LILRB4 legend colours must be constant across cohorts')
        colours = this_colours
        c.text(left, 5, 'ABC'[i], 10, True, color='#000000')
        c.text(left + 30, 5, cohort, 7.8, True, align='center')
        c.place('FS1_' + cohort, left, top)
    p = spec('FS1_' + COHORTS[0])
    centre_y = 9 + p['height_mm'] * (p['layer_box'][1] + p['layer_box'][3] / 2) / 100
    vertical_text(c, 2.8, centre_y, 'Cumulative proportion (%)')
    c.text(94, 61, 'Δ correlation (gated − ungated)', 7.5, align='center')
    c.line(49, 67.3, 54, 67.3, colours[0], .9)
    c.text(56, 68, 'Matched genes', 7.5)
    c.page.draw_line((112 * MM, 67.3 * MM), (117 * MM, 67.3 * MM),
                     color=rgb(colours[1]), width=.9, dashes='[3 2]')
    c.symbol(114.5, 67.3, colours[1], 'circle', .7)
    c.text(119, 68, 'LILRB4', 7.5)
    return finish('Figure_S1', c, {
        'source_verification': checks,
        'legend_colours': {'matched_genes': colours[0], 'LILRB4': colours[1]},
        'descriptive_only': True,
        'ECDF_smoothing': False,
        'midrank_not_P_value': True,
        'in_figure_N_delta_rank_removed': 'Moved to caption; no numeric source changed.',
        'scientific_changes': False,
    })


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--figures', nargs='+', choices=['3', '4', 'S1'], default=['3', '4', 'S1'])
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    for figure in args.figures:
        source_checks(REQUIRED[figure])
    if args.check_only:
        print('Source hashes and required Origin PDF presence passed; no figure composed.')
    else:
        for figure in args.figures:
            {'3': figure3, '4': figure4, 'S1': figureS1}[figure]()
        print('COMPOSED ' + ', '.join(args.figures) + '; actual visual QA remains required.')
