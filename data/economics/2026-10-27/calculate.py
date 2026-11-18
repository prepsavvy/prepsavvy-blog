"""Reproduce the PrepSavvy economics research index, edition 2026-10-27.

Run: python calculate.py
Standard library only. Reads works.jsonl and journals.json in this directory,
writes reproduced-index.csv, reproduced-index.json and
reproduced-country-shares.csv, and checks every
university's rank, paper count and scores against index.json (tolerance 1e-8).
"""
import csv, json, math
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
START, END, MIDPOINT, MINIMUM = 2015, 2024, 2019, 50
FIELDS = ['rank', 'institution', 'country', 'institution_id', 'top_decile_equivalent', 'top_decile_share_pct',
          'articles', 'fractional_articles', 'fractional_citations', 'articles_early', 'articles_recent',
          'output_change', 'output_change_pct']


def calculate(works, journals, minimum=MINIMUM):
    allowed = {j['source_id'] for j in journals}
    groups, ids, dois = defaultdict(list), set(), set()
    for w in works:
        if w['primary_location']['source']['id'] not in allowed:
            raise ValueError('Work journal is outside the journal list')
        if w['id'] in ids:
            raise ValueError('Duplicate work ID')
        ids.add(w['id'])
        doi = (w.get('doi') or '').strip().lower()
        if doi:
            if doi in dois:
                raise ValueError('Duplicate DOI')
            dois.add(doi)
        groups[(w['primary_location']['source']['id'], w['publication_year'])].append(w)
    if {y for _, y in groups} != set(range(START, END + 1)):
        raise ValueError('Incomplete publication years')

    # Top decile within each journal and year. Papers tied at the boundary
    # share the remaining credit, so each cohort carries exactly 10% of its papers.
    credits = {}
    for cohort in groups.values():
        counts = sorted((w['cited_by_count'] for w in cohort), reverse=True)
        target = len(counts) / 10
        boundary = counts[math.ceil(target) - 1]
        weight = (target - sum(n > boundary for n in counts)) / counts.count(boundary)
        for w in cohort:
            n = w['cited_by_count']
            credits[w['id']] = 1 if n > boundary else weight if n == boundary else 0

    # Each paper's credit is split equally among its distinct universities.
    schools = {}
    for w in works:
        insts = {i['id']: i for a in w['authorships'] for i in a['institutions'] if i.get('type') == 'education'}
        for iid, i in insts.items():
            s = schools.setdefault(iid, {'institution_id': iid, 'institution': i['display_name'],
                'country': i.get('country_code'), 'articles': 0, 'fractional_articles': 0.,
                'top_decile_equivalent': 0., 'fractional_citations': 0., 'articles_early': 0, 'articles_recent': 0})
            f = 1 / len(insts)
            s['articles'] += 1
            s['fractional_articles'] += f
            s['top_decile_equivalent'] += credits[w['id']] * f
            s['fractional_citations'] += w['cited_by_count'] * f
            s['articles_early' if w['publication_year'] <= MIDPOINT else 'articles_recent'] += 1

    total = sum(s['top_decile_equivalent'] for s in schools.values())
    by_country = defaultdict(float)
    for s in schools.values():
        by_country[s['country'] or 'unknown'] += s['top_decile_equivalent']
    countries = sorted(({'country': c, 'top_decile_equivalent': v, 'share_pct': 100 * v / total}
                        for c, v in by_country.items()), key=lambda r: -r['top_decile_equivalent'])

    eligible = sorted((s for s in schools.values() if s['articles'] >= minimum),
        key=lambda s: (-round(s['top_decile_equivalent'], 8), -round(s['fractional_citations'], 8), s['institution_id']))
    previous, rank = None, 0
    for pos, s in enumerate(eligible, 1):
        score = (round(s['top_decile_equivalent'], 8), round(s['fractional_citations'], 8))
        if score != previous:
            rank = pos
        previous = score
        s['rank'] = rank
        s['top_decile_share_pct'] = 100 * s['top_decile_equivalent'] / s['fractional_articles']
        s['output_change'] = s['articles_recent'] - s['articles_early']
        s['output_change_pct'] = 100 * s['output_change'] / s['articles_early'] if s['articles_early'] else None
    return eligible, countries


def main():
    works = [json.loads(line) for line in (HERE / 'works.jsonl').read_text(encoding='utf-8').splitlines() if line]
    journals = json.loads((HERE / 'journals.json').read_text(encoding='utf-8'))
    rows, countries = calculate(works, journals)
    with open(HERE / 'reproduced-country-shares.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['country', 'top_decile_equivalent', 'share_pct'])
        writer.writeheader()
        writer.writerows(countries)
    with open(HERE / 'reproduced-index.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows({k: r[k] for k in FIELDS} for r in rows)
    (HERE / 'reproduced-index.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding='utf-8')
    published = {r['institution_id']: r for r in json.loads((HERE / 'index.json').read_text(encoding='utf-8'))}
    if set(published) != {r['institution_id'] for r in rows}:
        raise SystemExit('MISMATCH: different set of universities')
    for r in rows:
        p = published[r['institution_id']]
        if (r['rank'] != p['rank'] or r['articles'] != p['articles']
                or abs(r['top_decile_equivalent'] - p['top_decile_equivalent']) > 1e-8
                or abs(r['fractional_citations'] - p['fractional_citations']) > 1e-8):
            raise SystemExit('MISMATCH: ' + r['institution'])
    print(f'Reproduced {len(rows)} universities from {len(works)} papers; every rank and score matches index.json.')


if __name__ == '__main__':
    main()
