"""Derive NYU's venue comparison from the frozen article records."""
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / '2026-10-23'

def nyu_journals():
    schools = list(csv.DictReader((DATA / 'schools.csv').open(encoding='utf-8')))
    institution = next(r['institution_id'] for r in schools if r['institution'] == 'New York University')
    counts = defaultdict(lambda: [0, 0])
    for line in (DATA / 'works.jsonl').open(encoding='utf-8'):
        work = json.loads(line)
        institutions = {i['id'] for a in work['authorships'] for i in a['institutions']}
        if institution in institutions:
            journal = work['primary_location']['source']['display_name']
            counts[journal][int(work['publication_year'] >= 2020)] += 1
    rows = [{'journal': name, 'articles_2015_2019': a, 'articles_2020_2024': b, 'change': b-a}
            for name, (a, b) in counts.items()]
    return sorted(rows, key=lambda r: (r['change'], r['journal']))

if __name__ == '__main__':
    rows = nyu_journals()
    assert sum(r['articles_2015_2019'] for r in rows) == 104
    assert sum(r['articles_2020_2024'] for r in rows) == 86
    out = ROOT / 'analysis' / '2026-10-23'
    out.mkdir(parents=True, exist_ok=True)
    with (out / 'nyu-journals.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print('NYU venue comparison verified: 104 to 86 articles')
