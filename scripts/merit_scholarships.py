"""Offline reproduction of scholarship cash-tier charts from the frozen public bundle."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from matplotlib.ticker import FuncFormatter

from chart_theme import BLUE, GREEN, GRID, ROOT, canvas, plt, save

DEFAULT_DATA = ROOT / 'data/act-scholarships/2026-10-26'
DEFAULT_OUTPUT = ROOT / 'figures/act-scholarships/2026-10-26'
PANELS = [
    {'id': 'ua', 'name': 'University of Alabama', 'gpa': 3.75, 'gpa_label': 'Published GPA condition: 3.50+', 'threshold': [29, 30], 'expected': [15000, 24000], 'policy': 'Single official test date'},
    {'id': 'uab', 'name': 'University of Alabama at Birmingham', 'gpa': 3.75, 'gpa_label': 'Published GPA condition: 3.50–3.99', 'threshold': [31, 32], 'expected': [17500, 22500], 'policy': 'No superscore'},
    {'id': 'una', 'name': 'University of North Alabama', 'gpa': 3.75, 'gpa_label': 'Published unweighted GPA condition: 3.51–4.00', 'threshold': [29, 30], 'expected': [8500, 10000], 'policy': 'ACT superscore: English, Reading and Math'},
]


class AmbiguousBandsError(ValueError):
    pass


def load_bundle(directory=DEFAULT_DATA):
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
    for filename, expected in manifest['files'].items():
        if Path(filename).name != filename:
            raise ValueError('Manifest file must stay within the edition directory')
        actual = hashlib.sha256((directory / filename).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f'Frozen data checksum mismatch: {filename}')
    bundle = json.loads((directory / 'merit.json').read_text(encoding='utf-8'))
    if len(bundle['offers']) != manifest['band_records'] or manifest['band_records'] != 47:
        raise ValueError('Expected 47 normalized band records')
    ids = [row['record_id'] for row in bundle['offers']]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate normalized band IDs')
    if {row['institution_id'] for row in bundle['offers']} != {'ua', 'uab', 'una'}:
        raise ValueError('Unexpected institution coverage')
    if any(row['entry_year'] != 2027 or row['entry_term'] != 'fall' for row in bundle['offers']):
        raise ValueError('Incompatible intake in frozen data')
    return bundle, manifest


def matched_band(offers, institution_id, score, gpa, exam='ACT'):
    if exam != 'NONE' and score is None:
        raise ValueError('A numeric exam route needs a score')
    matches = []
    for row in offers:
        if row['institution_id'] != institution_id or row['exam'] != exam:
            continue
        if gpa < row['gpa_min'] or (row['gpa_max'] is not None and gpa > row['gpa_max']):
            continue
        if exam != 'NONE' and not row['score_min'] <= score <= row['score_max']:
            continue
        matches.append(row)
    if not matches:
        raise LookupError(f'No published band for {institution_id}/{exam}/{score}/GPA {gpa}')
    if len(matches) > 1:
        raise AmbiguousBandsError(f'Overlapping alternatives need manual review: {institution_id}/{exam}/{score}/GPA {gpa}')
    return matches[0]


def annual_cash(row):
    if row['award_kind'] != 'cash' or row['annual_amount_min'] != row['annual_amount_max']:
        raise ValueError('A range or tuition package has no single comparable annual cash value')
    return row['annual_amount_min']


def panel_data(offers, panel):
    steps = []
    for score in range(20, 37):
        try:
            row = matched_band(offers, panel['id'], score, panel['gpa'])
            amount = annual_cash(row)
            record_id = row['record_id']
        except LookupError:
            amount, record_id = None, None
        steps.append({'score': score, 'annual_cash_usd': amount, 'record_id': record_id})
    before, after = [annual_cash(matched_band(offers, panel['id'], score, panel['gpa'])) for score in panel['threshold']]
    if [before, after] != panel['expected']:
        raise ValueError(f"Published threshold claim no longer matches frozen data: {panel['id']}")
    return {'institution_id': panel['id'], 'gpa_for_selection': panel['gpa'], 'published_gpa_label': panel['gpa_label'], 'cash_only': True, 'threshold': panel['threshold'], 'before': before, 'after': after, 'increase': after - before, 'steps': steps}


def render(data_dir=DEFAULT_DATA, output=DEFAULT_OUTPUT):
    bundle, manifest = load_bundle(data_dir)
    panels = [panel_data(bundle['offers'], panel) for panel in PANELS]
    fig, initial_axis = canvas('Where one ACT point changes the award tier',
        'Annual cash awards for fall 2027 entry. Each panel holds its own published GPA condition constant.', height=9.3, left=.11)
    initial_axis.remove()
    positions = [.665, .425, .185]
    for spec, data, position in zip(PANELS, panels, positions):
        ax = fig.add_axes([.11, position, .83, .16])
        x = np.array([row['score'] for row in data['steps']])
        y = np.array([np.nan if row['annual_cash_usd'] is None else row['annual_cash_usd'] for row in data['steps']])
        ax.step(x, y, where='post', color=BLUE, linewidth=2.5)
        threshold_before, threshold_after = spec['threshold']
        ax.plot([threshold_after, threshold_after], [data['before'], data['after']], color=GREEN, linewidth=4, zorder=4)
        ax.scatter([threshold_before, threshold_after], [data['before'], data['after']], color=[BLUE, GREEN], s=42, zorder=5)
        ax.text(.57, .95, f"ACT {threshold_before} → {threshold_after}: +${data['increase']:,}/year", transform=ax.transAxes, color=GREEN, fontsize=10, weight='bold', va='center')
        ax.set_title(spec['name'], loc='left', fontsize=12, weight='bold', pad=30)
        ax.text(0, 1.075, spec['gpa_label'] + '  |  ' + spec['policy'], transform=ax.transAxes, fontsize=8.5)
        ax.set_xlim(20, 36.8)
        ax.set_ylim(0, 32000)
        ax.set_xticks(sorted({20, 24, 28, 32, 36, threshold_before, threshold_after}))
        ax.set_yticks([0, 10000, 20000, 30000])
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: '$0' if value == 0 else f'${value / 1000:.0f}k'))
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, color=GRID)
        ax.tick_params(length=0, pad=6)
        ax.spines['bottom'].set_color(GRID)
    fig.text(.11, .137, 'ACT score on the university’s stated scholarship basis', fontsize=9)
    fig.text(.025, .095, 'North Alabama’s Presidential tier also adds conditional residence-hall funding: $4,000/year for two years.', fontsize=8.5)
    fig.text(.025, .073, 'Cash tiers are not net prices. Residency, citizenship and GPA rules differ; these are not identical applicant comparisons.', fontsize=8.2)
    output = Path(output)
    save(fig, output, 'annual-award-tiers', 'Sources: official university scholarship pages, checked 26 October 2026.')
    receipt = {'study': manifest['study'], 'edition': manifest['edition'], 'input_file_sha256': manifest['files'], 'normalized_band_records': 47, 'panels': panels, 'source_receipts': bundle['sources']}
    (output / 'chart-inputs.json').write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(output), 'panels': len(panels), 'band_records': 47}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=DEFAULT_DATA)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    render(args.data, args.output)
