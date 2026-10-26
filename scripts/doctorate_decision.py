"""Offline reproduction of scoped SED 2025 doctorate-decision evidence.

The calculator uses Python standard library only; rendering optionally uses Matplotlib.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/philosophy-doctorates/2026-10-27'
OUTPUT = ROOT/'figures/philosophy-doctorates/2026-10-27'
PHIL_REL = 'Philosophy and religious studies'
DETAILS = ['Philosophy', 'Religion/ religious studies', 'Philosophy and religious studies nec']
US_COLUMNS = ['All doctorate recipients', 'Definite commitments (all locations)',
              'United States total', 'United States postdoctoral study',
              'United States academic employment', 'United States industry employment',
              'United States other sector or unknown', 'Abroad', 'Location unknown']

def find(records, table, scope, row_prefix, column=None, section=None, group='All'):
    matches = [r for r in records if r['table'] == table and r['field_scope'] == scope
               and r['subpopulation'] == group and r['row_label'].startswith(row_prefix)
               and (column is None or r['column_label'] == column)
               and (section is None or r['section'] == section)]
    if len(matches) != 1:
        raise ValueError(f'Ambiguous/missing source measure {table}/{scope}/{row_prefix}: {len(matches)}')
    return matches[0]

def summarize(records):
    def value(*args, **kwargs):
        r = find(records, *args, **kwargs)
        if r['status'] != 'reported':
            raise ValueError('A required narrative value is not disclosed')
        return r['value']
    awards = {scope: value('3-1', scope, scope, column='2025') for scope in [PHIL_REL, *DETAILS]}
    if sum(awards[s] for s in DETAILS) != awards[PHIL_REL]:
        raise ValueError('Detailed fields do not reconcile to combined major')
    taxonomy = {r['field_scope']: r['raw'] for r in records if r['table'] == 'A-4'}
    if taxonomy.get('Philosophy') != '38.01, 38.99' or float(taxonomy.get(PHIL_REL, 0)) != 38:
        raise ValueError('Philosophy taxonomy changed')
    profiles = {}
    for scope in ['Humanities', PHIL_REL]:
        total = value('8-15', scope, 'All doctorate recipients')
        reports = value('9-15', scope, 'Doctorate recipients reporting postgraduation status')
        definite = value('6-1', scope, scope, column='Definite commitments (all locations)')
        us = {col: value('6-1', scope, scope, column=col) for col in US_COLUMNS}
        if us['United States total'] != sum(us[c] for c in US_COLUMNS[3:7]):
            raise ValueError('US destination sectors do not reconcile')
        if definite != us['United States total']+us['Abroad']+us['Location unknown'] or total != us['All doctorate recipients']:
            raise ValueError('Commitment location/recipient totals do not reconcile')
        status = {name: value('9-15', scope, prefix) for name, prefix in [
            ('postdoc_percent', 'Definite postdoctoral training plans (%)'),
            ('employment_percent', 'Definite employment plans (%)'),
            ('seeking_percent', 'Seeking employment or study (%)'), ('other_percent', 'Other status (%)')]}
        if abs(sum(status.values())-100) > .21 or not 0 <= definite <= reports <= total:
            raise ValueError('Postgraduation status population mismatch')
        if abs(100*definite/reports-status['postdoc_percent']-status['employment_percent']) > .11:
            raise ValueError('Commitment count disagrees with rounded status percentages')
        profiles[scope] = {'field_total': total, 'years_since_bachelor_median': value('8-15', scope, 'Years since earning', group='All'),
            'years_from_graduate_start_median': value('8-15', scope, 'From graduate school start'),
            'years_from_defined_doctoral_start_median': value('8-15', scope, 'From doctoral program start'),
            'time_item_response_n': None, 'tuition_remission_percent': value('8-15', scope, 'Received tuition remission'),
            'tuition_item_response_n': None, 'postgraduation_status_reports': reports,
            'postgraduation_status_nonreporters': total-reports, 'status_percentages': status,
            'definite_commitments': definite, 'definite_percent_of_status_reporters': 100*definite/reports,
            'destination_counts': us,
            'employment_sectors_percent_of_definite_employment': {label: value('9-15', scope, label)
                for label in ['Academe', 'Government', 'Industry or business', 'Nonprofit organization', 'Other or unknown']}}
    if profiles[PHIL_REL]['field_total'] != awards[PHIL_REL]:
        raise ValueError('Award/profile major-field totals disagree')
    funding_n = value('4-1', 'Humanities', 'Humanities (number)')
    funding = {r['row_label']: r['value'] for r in records if r['table'] == '4-1' and r['unit'] == 'percent'}
    if abs(sum(funding.values())-100) > .21:
        raise ValueError('Primary source categories do not reconcile')
    debts = {}
    for section in ['Cumulative debt', 'Graduate debt', 'Undergraduate debt']:
        denom = value('4-4', 'Humanities', 'All reporting', column='Number or median', section=section)
        no_debt = value('4-4', 'Humanities', 'No debt', column='Number or median', section=section)
        buckets = [r for r in records if r['table'] == '4-4' and r['section'] == section
                   and r['column_label'] == 'Number or median' and (r['row_label'] == 'No debt' or r['row_label'].startswith('$'))]
        if any(r['status'] != 'reported' for r in buckets) or sum(r['value'] for r in buckets) != denom:
            raise ValueError('Humanities debt categories do not reconcile')
        debts[section] = {'field_scope': 'Humanities', 'respondents': denom, 'no_debt_count': no_debt,
            'no_debt_percent': value('4-4', 'Humanities', 'No debt', column='Percent', section=section),
            'positive_debt_count': denom-no_debt,
            'median_among_positive_debt_only_usd': value('4-4', 'Humanities', 'Median debt', column='Number or median', section=section)}
        if abs(100*no_debt/denom-debts[section]['no_debt_percent']) > .051:
            raise ValueError('Debt count and rounded percentage disagree')
    return {'status': 'computed_frozen_edition', 'survey_year': 2025, 'philosophy_detailed_awards': awards,
            'taxonomy': taxonomy, 'profiles': profiles,
            'primary_support': {'field_scope': 'Humanities', 'respondents': funding_n, 'percentages': funding},
            'debt': debts,
            'interpretation': 'Recipients, not entrants. No completion probabilities, philosophy-only funding estimates or causal ROI.'}


def validate(cells):
    ids = set()
    for c in cells:
        if c['record_id'] in ids or c['record_id'] != c['table']+':'+c['cell']:
            raise ValueError('Duplicate or inconsistent source-cell identity')
        ids.add(c['record_id'])
        if c['survey_year'] != 2025 or not c['source_url'].startswith('https://ncses.nsf.gov/'):
            raise ValueError('Wrong source year or authority')
        if c['status'] == 'reported':
            if type(c['raw']) not in (int, float) or type(c['value']) not in (int, float) or not math.isfinite(c['raw']) or c['raw'] != c['value'] or c['value'] < 0:
                raise ValueError('Reported number differs from raw cell')
        elif c['status'] == 'taxonomy_code':
            if c['table'] != 'A-4' or c['value'] is not None:
                raise ValueError('Taxonomy code treated as numeric evidence')
        else:
            tokens = {'suppressed': 'D', 'not_calculable': '-', 'not_available': 'NA'}
            if c['status'] not in tokens or c['raw'] != tokens[c['status']] or c['value'] is not None:
                raise ValueError('Missing or suppressed cell converted into a number')


def load(directory=DATA):
    root = Path(directory)
    manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest['files'].items():
        if Path(name).name != name or hashlib.sha256((root/name).read_bytes()).hexdigest() != expected:
            raise ValueError('Frozen edition hash mismatch')
    cells = json.loads((root/'cells.json').read_text(encoding='utf-8'))
    validate(cells)
    if len(cells) != manifest['source_cells'] or sum(c['status'] == 'suppressed' for c in cells) != manifest['suppressed_cells']:
        raise ValueError('Source-cell or suppression count mismatch')
    return cells, manifest


def replay_workbooks(cells, manifest, cache):
    """Verify exact original XLSX bytes and selected cells using only stdlib XML."""
    ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    by_url = {}
    for source in manifest['source_files']:
        if not source['url'].endswith('.xlsx'):
            continue
        path = Path(cache)/source['sha256']
        if not path.exists():
            path = Path(cache)/source['url'].rsplit('/', 1)[1]
        if hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']:
            raise ValueError('Official workbook checksum differs')
        with zipfile.ZipFile(path) as z:
            strings = []
            if 'xl/sharedStrings.xml' in z.namelist():
                for item in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si', ns):
                    strings.append(''.join(x.text or '' for x in item.findall('.//s:t', ns)))
            values = {}
            for cell in ET.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('.//s:c', ns):
                kind = cell.get('t')
                v = cell.find('s:v', ns)
                if kind == 'inlineStr':
                    value = ''.join(t.text or '' for t in cell.findall('.//s:t', ns))
                elif v is None:
                    continue
                elif kind == 's':
                    value = strings[int(v.text)]
                elif kind == 'str':
                    value = v.text
                else:
                    value = float(v.text)
                values[cell.get('r')] = value
            by_url[source['url']] = values
    for c in cells:
        if by_url[c['source_url']][c['cell']] != c['raw']:
            raise ValueError('Raw source workbook cell differs')
    return {'workbooks': len(by_url), 'selected_cells': len(cells)}


def render(result, output):
    from chart_theme import BLUE, GREEN, canvas, save
    p = result['profiles'][PHIL_REL]
    fig, ax = canvas('The time commitment behind a doctorate',
        '2025 recipients in Philosophy and religious studies; median years', height=5.1, left=.40)
    labels = ["Since the bachelor's degree", 'From graduate-school start', 'From defined doctoral-program start']
    values = [p['years_since_bachelor_median'], p['years_from_graduate_start_median'], p['years_from_defined_doctoral_start_median']]
    ax.barh(range(3), values, color=[BLUE, BLUE, GREEN], height=.48)
    ax.set_yticks(range(3), labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 12.5)
    ax.set_xticks([0, 3, 6, 9, 12])
    ax.set_xlabel('Median years')
    for i, v in enumerate(values):
        ax.text(v+.2, i, f'{v:.1f}', va='center', weight='bold')
    fig.subplots_adjust(bottom=.25)
    fig.text(.025, .12, "Defined doctoral start can include a related master's. Time-item response counts are not printed.", fontsize=8)
    save(fig, output, 'time-to-doctorate', 'Source: NCSES, Survey of Earned Doctorates 2025, Table 8-15; released September 2026.')

    fig, ax = canvas('What recipients reported at graduation',
        'Philosophy and religious studies; 538 recipients reporting postgraduation status', height=5.6, left=.32)
    labels = ['Definite employment', 'Postdoctoral training', 'Seeking employment or study', 'Other status']
    keys = ['employment_percent', 'postdoc_percent', 'seeking_percent', 'other_percent']
    values = [p['status_percentages'][k] for k in keys]
    ax.barh(range(4), values, color=[BLUE, GREEN, BLUE, BLUE], height=.5)
    ax.set_yticks(range(4), labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 46)
    ax.set_xticks([0, 10, 20, 30, 40], ['0%', '10%', '20%', '30%', '40%'])
    for i, v in enumerate(values):
        ax.text(v+.7, i, f'{v:.1f}%', va='center', weight='bold')
    fig.subplots_adjust(bottom=.23)
    fig.text(.025, .12, '90 of 628 recipients did not report status. Employment includes returning to predoctoral employment.', fontsize=8)
    save(fig, output, 'plans-at-graduation', 'Source: NCSES, Survey of Earned Doctorates 2025, Tables 9-15 and 6-1; September 2026.')
    for name in ['time-to-doctorate.svg', 'plans-at-graduation.svg']:
        path = output/name
        path.write_bytes(b'\n'.join(line.rstrip(b' \t\r') for line in path.read_bytes().splitlines())+b'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=DATA)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--no-charts', action='store_true')
    parser.add_argument('--raw-cache-dir', type=Path)
    args = parser.parse_args()
    cells, manifest = load(args.data)
    result = summarize(cells)
    if args.raw_cache_dir:
        print(json.dumps({'source_replay': replay_workbooks(cells, manifest, args.raw_cache_dir)}))
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'chart-inputs.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
    if not args.no_charts:
        render(result, args.output)
    print(json.dumps({'source_cells': len(cells), 'philosophy_awards': result['philosophy_detailed_awards']['Philosophy'],
                      'combined_field_status_reports': result['profiles'][PHIL_REL]['postgraduation_status_reports']}))


if __name__ == '__main__':
    main()
