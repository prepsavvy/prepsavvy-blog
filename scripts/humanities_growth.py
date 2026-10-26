"""Recalculate humanities award trends from the frozen, public IPEDS extract."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

FAMILIES = {'16': 'Languages and linguistics', '23': 'English and writing',
            '38': 'Philosophy and religious studies', '54': 'History',
            '24': 'Humanistic studies'}


def family(cip):
    if cip == '24.0103':
        return FAMILIES['24']
    if re.fullmatch(r'(16|23|38|54)\.[0-9]{4}', cip):
        return FAMILIES[cip[:2]]
    raise ValueError(f'Out-of-scope or aggregate CIP code: {cip}')


def calculate(rows, years, minimum_baseline=100):
    a, b = years
    if a >= b:
        raise ValueError('Award years must be ordered')
    totals, meta, by_family, by_code, seen = {}, {}, defaultdict(Counter), defaultdict(Counter), set()
    for r in rows:
        y, unit, code, count = int(r['year']), r['unitid'], r['cipcode'], int(r['awards'])
        key = (y, unit, code)
        if key in seen or y not in years or count < 0:
            raise ValueError('Duplicate, out-of-period or negative source record')
        seen.add(key)
        meta[(y, unit)] = {k: r[k] for k in ['institution', 'state', 'city', 'control', 'sector']}
        if code == '99':
            totals[(y, unit)] = count
        else:
            by_family[(y, unit)][family(code)] += count
            by_code[(y, unit)][code] += count
    if set(y for y, _ in totals) != set(years) or any(k not in totals for k in by_family):
        raise ValueError('Missing year or institution total')
    national, institutions, subjects = [], [], []
    for y in years:
        awards = sum(sum(v.values()) for (yr, _), v in by_family.items() if yr == y)
        national.append({'year': y, 'humanities_awards': awards,
                         'bachelor_awards': sum(n for (yr, _), n in totals.items() if yr == y)})
    for (y, unit), total in totals.items():
        if sum(by_family[(y, unit)].values()) > total:
            raise ValueError('Humanities subtotal exceeds institution bachelor total')
        if y != b or (a, unit) not in totals:
            continue
        n0, n1 = sum(by_family[(a, unit)].values()), sum(by_family[(b, unit)].values())
        t0, t1 = totals[(a, unit)], total
        row = {'unitid': unit, **meta[(b, unit)], 'baseline_awards': n0, 'latest_awards': n1,
               'change_awards': n1-n0, 'change_pct': 100*(n1/n0-1) if n0 else None,
               'baseline_all_bachelors': t0, 'latest_all_bachelors': t1,
               'baseline_share_pct': 100*n0/t0 if t0 else None,
               'latest_share_pct': 100*n1/t1 if t1 else None,
               'control_changed': meta[(a, unit)]['control'] != meta[(b, unit)]['control']}
        row['share_change_pp'] = row['latest_share_pct']-row['baseline_share_pct'] if t0 and t1 else None
        institutions.append(row)
        for f in FAMILIES.values():
            x, z = by_family[(a, unit)][f], by_family[(b, unit)][f]
            subjects.append({'unitid': unit, 'institution': row['institution'], 'subject': f,
                             'baseline_awards': x, 'latest_awards': z, 'change_awards': z-x})
    public = sorted([r for r in institutions if r['control']=='1' and not r['control_changed']
                     and r['baseline_awards']>=minimum_baseline],
                    key=lambda r: (-r['change_awards'], r['unitid']))
    national_subjects = []
    for f in FAMILIES.values():
        x, z = [sum(v[f] for (y, _), v in by_family.items() if y==yr) for yr in years]
        national_subjects.append({'subject': f, 'baseline_awards': x, 'latest_awards': z,
                                 'change_awards': z-x, 'change_pct': 100*(z/x-1) if x else None})
    return {'years': years, 'minimum_baseline': minimum_baseline, 'national': national,
            'national_subjects': national_subjects, 'institutions': institutions,
            'public_growth': public, 'institution_subjects': subjects}


def write_csv(path, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build(data, output):
    manifest = json.loads((data/'manifest.json').read_text(encoding='utf-8'))
    for filename, digest in manifest['files'].items():
        if hashlib.sha256((data/filename).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Source checksum mismatch: {filename}')
    with (data/'program-awards.csv').open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    if len(rows) != manifest['records']:
        raise ValueError('Source record count mismatch')
    result = calculate(rows, manifest['years'])
    if result['national'] != manifest['national_totals']:
        raise ValueError('Independent national calculation differs from warehouse export')
    output.mkdir(parents=True, exist_ok=True)
    for name in ['national', 'national_subjects', 'institutions', 'public_growth', 'institution_subjects']:
        write_csv(output/(name.replace('_','-')+'.csv'), result[name])
    (output/'summary.json').write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps({'state': 'verified', 'source_rows': len(rows), 'matched_institutions': len(result['institutions']),
                      'eligible_public_institutions': len(result['public_growth']), 'national': result['national']}))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    build(args.data, args.output)
