"""Offline philosophy outcomes calculator; plotting is optional.

python scripts/philosophy_outcomes.py --no-charts
python scripts/philosophy_outcomes.py
python scripts/philosophy_outcomes.py --raw-zip /path/to/official.zip --no-charts
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/philosophy-outcomes/2026-10-27'
OUTPUT = ROOT / 'figures/philosophy-outcomes/2026-10-27'
UC = {'001312': 'UC Berkeley', '001313': 'UC Davis', '001315': 'UCLA',
      '001316': 'UC Riverside', '001320': 'UC Santa Barbara', '001321': 'UC Santa Cruz'}


def decoded(raw):
    if raw == 'PS':
        return {'raw': raw, 'status': 'privacy_suppressed', 'value': None}
    if raw in {'NA', 'NULL', ''}:
        return {'raw': raw, 'status': 'not_available', 'value': None}
    if not isinstance(raw, str) or not re.fullmatch(r'\d+', raw):
        raise ValueError('Unrecognized source value')
    return {'raw': raw, 'status': 'reported', 'value': int(raw)}


def validate(records):
    seen, unitids = set(), set()
    controls = {'Public', 'Private, nonprofit', 'Private, for-profit', 'Foreign'}
    for r in records:
        key = f"{r['opeid6']}:3801:3"
        if r['record_id'] != key or key in seen or not re.fullmatch(r'\d{6}', r['opeid6']):
            raise ValueError('Invalid or duplicated program group')
        seen.add(key)
        if r['cip4'] != '3801' or r['credential_code'] != '3' or r['credential'] != "Bachelor's Degree":
            raise ValueError('Philosophy bachelor scope changed')
        if r['control'] not in controls or r['domestic_scope'] != (r['control'] != 'Foreign'):
            raise ValueError('Domestic scope inconsistent with source control')
        identifiers = [u for u in r['unitids'] if u not in {'NA', 'NULL', ''}]
        if len(identifiers) != len(set(identifiers)) or unitids.intersection(identifiers):
            raise ValueError('Repeated branch identifier')
        if r['domestic_scope'] and len(identifiers) != len(r['unitids']):
            raise ValueError('Domestic institution lacks a UNITID')
        unitids.update(identifiers)
        if len(r['unitids']) != len(r['branch_names']) or not r['unitids']:
            raise ValueError('Incomplete branch provenance')
        if r['pooled_branch_group'] != (len(r['unitids']) > 1):
            raise ValueError('Branch pooling flag inconsistent')
        if r['pooled_branch_group'] and 'pooled' not in r['display_name']:
            raise ValueError('Pooled outcomes require an explicit pooled label')
        for section in ['measures', 'national']:
            for m in r[section].values():
                if m != decoded(m['raw']):
                    raise ValueError('Numeric value or suppression status disagrees with raw source')
    if not records:
        raise ValueError('No program records')


def load(directory=DATA):
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
    for name, digest in manifest['files'].items():
        if Path(name).name != name:
            raise ValueError('Manifest path escapes edition')
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Frozen checksum mismatch: {name}')
    records = json.loads((directory / 'programs.json').read_text(encoding='utf-8'))
    validate(records)
    if len(records) != manifest['source_record_count']:
        raise ValueError('Source group count mismatch')
    return records, manifest


def calculate(records, floor=30):
    validate(records)
    domestic = [r for r in records if r['domestic_scope']]
    coverage = {k: dict(Counter(r['measures'][k]['status'] for r in domestic))
                for k in records[0]['measures']}
    national = {}
    for key in records[0]['national']:
        values = {r['national'][key]['value'] for r in records if r['national'][key]['status'] == 'reported'}
        if len(values) != 1:
            raise ValueError('Absent or conflicting publisher national benchmark')
        national[key] = values.pop()
    comparison = []
    for r in domestic:
        m = r['measures']
        if m['EARN_MDN_4YR']['value'] is not None and m['EARN_COUNT_WNE_4YR']['value'] is not None and m['EARN_COUNT_WNE_4YR']['value'] >= floor:
            comparison.append({'opeid6': r['opeid6'], 'name': r['display_name'], 'control': r['control'],
                'earnings': m['EARN_MDN_4YR']['value'], 'earnings_n': m['EARN_COUNT_WNE_4YR']['value'],
                'debt': m['DEBT_ALL_STGP_ANY_MDN'], 'debt_n': m['DEBT_ALL_STGP_ANY_N'],
                'pooled': r['pooled_branch_group'], 'branches': r['branch_names']})
    comparison.sort(key=lambda r: r['opeid6'])
    uc_source = [r for r in domestic if r['display_name'].startswith('University of California-')]
    uc = [{**r, 'label': UC.get(r['opeid6'], r['name'].replace('University of California-', 'UC '))}
          for r in comparison if r['name'].startswith('University of California-')]
    uc_ids = {r['opeid6'] for r in uc}
    uc_scope = {'rule': 'All non-foreign University of California program groups with disclosed four-year earnings and at least 30 disclosed earnings observations; debt availability is not an eligibility condition.',
        'source_uc_groups': len(uc_source), 'included': len(uc),
        'omitted': [{'opeid6': r['opeid6'], 'name': r['display_name'],
                     'earnings': r['measures']['EARN_MDN_4YR'],
                     'earnings_n': r['measures']['EARN_COUNT_WNE_4YR']}
                    for r in uc_source if r['opeid6'] not in uc_ids]}
    return {'source_groups': len(records), 'source_unitid_rows': sum(len(r['unitids']) for r in records),
            'domestic_groups': len(domestic), 'domestic_unitid_rows': sum(len(r['unitids']) for r in domestic),
            'foreign_audit_groups': len(records) - len(domestic), 'coverage': coverage,
            'both_earnings_and_debt': sum(r['measures']['EARN_MDN_4YR']['value'] is not None and r['measures']['DEBT_ALL_STGP_ANY_MDN']['value'] is not None for r in domestic),
            'comparison_floor': floor, 'comparison': comparison, 'public_comparison_count': sum(r['control'] == 'Public' for r in comparison),
            'national_benchmark': national, 'uc_comparison': uc, 'uc_scope': uc_scope}


def raw_replay(path, records, manifest):
    """Optional stdlib-only replay from the exact official ZIP, without network calls."""
    zip_source = next(s for s in manifest['source_files'] if s['url'].endswith('.zip'))
    if hashlib.sha256(Path(path).read_bytes()).hexdigest() != zip_source['sha256']:
        raise ValueError('Official ZIP hash differs from frozen acquisition')
    grouped = defaultdict(list)
    with zipfile.ZipFile(path) as z:
        members = z.infolist()
        if len(members) != 1 or members[0].filename != 'Most-Recent-Cohorts-Field-of-Study.csv' or members[0].file_size > 300_000_000:
            raise ValueError('Unexpected source ZIP')
        with z.open(members[0]) as stream:
            for r in csv.DictReader(io.TextIOWrapper(stream, encoding='utf-8-sig')):
                if r['CIPCODE'] == '3801' and r['CREDLEV'] == '3':
                    grouped[r['OPEID6']].append(r)
    if set(grouped) != {r['opeid6'] for r in records}:
        raise ValueError('Raw source program coverage differs')
    for r in records:
        branches = grouped[r['opeid6']]
        if sorted(b['UNITID'] for b in branches) != r['unitids'] or sorted(b['INSTNM'] for b in branches) != r['branch_names']:
            raise ValueError('Raw branch mapping differs')
        if any(b['CONTROL'] != r['control'] or b['CIPDESC'] != 'Philosophy.' or b['CREDDESC'] != "Bachelor's Degree" for b in branches):
            raise ValueError('Raw control or credential differs')
        for section in ['measures', 'national']:
            for key, value in r[section].items():
                if any(decoded(b[key]) != value for b in branches):
                    raise ValueError(f'Raw source outcome differs: {key}')
    return {'verified_groups': len(records), 'verified_unitid_rows': sum(len(x) for x in grouped.values()), 'official_zip_sha256': zip_source['sha256']}


def render(summary, output):
    from matplotlib.ticker import FuncFormatter
    from chart_theme import BLUE, GREEN, GRID, canvas, save
    n = summary['national_benchmark']
    fig, ax = canvas('What philosophy graduates earn four years later',
        'Scorecard national benchmark: annual earnings in 2024 dollars', height=4.7, left=.09)
    fig.subplots_adjust(bottom=.25)
    ax.set_xlim(0, 95000)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xticks([0, 20000, 40000, 60000, 80000])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'${int(x/1000)}k'))
    ax.hlines(.5, n['EARN_P25_4YR_NAT'], n['EARN_P75_4YR_NAT'], color=BLUE, linewidth=12, alpha=.85)
    ax.scatter([n['EARN_MDN_4YR_NAT']], [.5], color=GREEN, s=180, zorder=4, edgecolors='white', linewidths=2)
    for key, y, label in [('EARN_P25_4YR_NAT', .25, '25th percentile'), ('EARN_MDN_4YR_NAT', .78, 'Median'), ('EARN_P75_4YR_NAT', .25, '75th percentile')]:
        ax.text(n[key], y, f"${n[key]:,}\n{label}", ha='center', va='center', color=GREEN if label == 'Median' else BLUE, fontsize=11, weight='bold')
    fig.text(.025, .12, f"{n['EARN_COUNT_WNE_4YR_NAT']:,} federally aided completers who worked and were not enrolled during measurement.", fontsize=8)
    save(fig, output, 'national-earnings-range', 'Source: U.S. Department of Education, College Scorecard, 15 October 2026 release.')

    rows = summary['uc_comparison']
    fig, ax = canvas('Philosophy earnings differ across UC program groups',
        'Four years after completion; 2024 dollars. Each label includes the disclosed earnings count.', height=6, left=.23)
    ax.set_xlim(40000, 83000)
    ax.set_ylim(-.6, len(rows)-.4)
    ax.set_yticks(range(len(rows)), [r['label'] for r in rows])
    ax.invert_yaxis()
    ax.set_xticks([40000, 50000, 60000, 70000, 80000])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'${int(x/1000)}k'))
    ax.axvline(n['EARN_MDN_4YR_NAT'], color=GREEN, linestyle='--', linewidth=1.5, alpha=.8)
    ax.hlines(range(len(rows)), 40000, [r['earnings'] for r in rows], color=GRID, linewidth=2)
    ax.scatter([r['earnings'] for r in rows], range(len(rows)), color=BLUE, s=65, zorder=3)
    for i, r in enumerate(rows):
        ax.text(r['earnings']+900, i, f"${r['earnings']:,}  ·  n={r['earnings_n']}", va='center', fontsize=9,
                bbox={'facecolor': 'white', 'edgecolor': 'none', 'pad': 2})
    fig.text(.025, .105, 'Dashed line: $54,455 Scorecard national benchmark. Six disclosed groups with earnings counts of at least 30.', fontsize=8)
    save(fig, output, 'uc-program-earnings', 'Source: U.S. Department of Education, College Scorecard, 15 October 2026 release.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=DATA)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--no-charts', action='store_true')
    parser.add_argument('--raw-zip', type=Path)
    args = parser.parse_args()
    records, manifest = load(args.data)
    result = calculate(records)
    if args.raw_zip:
        print(json.dumps({'raw_replay': raw_replay(args.raw_zip, records, manifest)}))
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'chart-inputs.json').write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    if not args.no_charts:
        render(result, args.output)
    print(json.dumps({k:result[k] for k in ['source_groups','domestic_groups','both_earnings_and_debt','public_comparison_count']}))


if __name__ == '__main__':
    main()
