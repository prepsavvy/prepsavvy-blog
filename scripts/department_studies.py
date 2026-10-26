"""Reproduce a frozen PrepSavvy institutional journal-research edition.

Standard-library only. No network, private repository, API key or BigQuery needed.
The institution-only input records have already passed the edition's recorded
raw-affiliation review; the included rules retain exact deterministic behavior.
"""
import argparse
import csv
import hashlib
import json
import math
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

AFFILIATION_RULES = {'reject_pattern': '(?!)', 'aliases': {}, 'overrides': {}}
DEPARTMENT_AFFILIATION_DECISIONS = {'overrides': {}, 'institution_overrides': {}}

def review_affiliations(works):
    """Remove acknowledgment-derived credit; preserve direct clean support.

    Flagged authorships retain only institution names or explicit aliases found
    in a separate non-acknowledgment affiliation string. Unsupported credit is
    withheld. The work remains in its journal/year citation reference cohort.
    Source-based corrections are explicit, versioned and independently inspectable.
    """
    def normalized(s):
        s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
        return re.sub('[^a-z0-9]','',s)
    pattern=re.compile(AFFILIATION_RULES['reject_pattern'],re.I)
    output=[];audit=[]
    for w in works:
        revised=dict(w);authors=[]
        override=AFFILIATION_RULES['overrides'].get(w['id'])
        for position,a in enumerate(w['authorships']):
            b=dict(a);strings=[s for s in a.get('raw_affiliation_strings',[]) if s]
            bad=[s for s in strings if pattern.search(s)]
            if override:
                b['institutions']=override['institutions']
            elif bad:
                clean=[normalized(s) for s in strings if not pattern.search(s)]
                retained=[]
                for i in a['institutions']:
                    aliases=[i['display_name'],*AFFILIATION_RULES['aliases'].get(i['id'],[])]
                    if any(normalized(alias) in s for alias in aliases for s in clean):retained.append(i)
                b['institutions']=retained
            if bad or override:
                audit.append({'work_id':w['id'],'doi':w.get('doi'),'authorship_position':position,
                  'decision':'primary_source_correction' if override else 'acknowledgment_filter',
                  'original_institutions':[i['id'] for i in a['institutions']],
                  'retained_institutions':[i['id'] for i in b['institutions']],
                  'source':override['source'] if override else w.get('doi'),
                  'raw_affiliation_sha256':hashlib.sha256(json.dumps(strings,ensure_ascii=False).encode()).hexdigest()})
            authors.append(b)
        revised['authorships']=authors;output.append(revised)
    return output,audit


def review_department_affiliations(works):
    typed, taxonomy_audit = [], []
    for work in works:
        authors = []
        for author in work['authorships']:
            institutions = []
            for institution in author['institutions']:
                decision = DEPARTMENT_AFFILIATION_DECISIONS.get('institution_overrides', {}).get(institution['id'])
                if decision:
                    original_type = institution.get('openalex_original_type', institution.get('type'))
                    institution = {**institution, 'openalex_original_type': original_type, 'type': decision['type']}
                    taxonomy_audit.append({'work_id': work['id'], 'institution_id': institution['id'],
                        'decision': 'source_verified_institution_type', 'original_type': original_type,
                        'corrected_type': decision['type'], 'source': decision['source']})
                institutions.append(institution)
            authors.append({**author, 'institutions': institutions})
        typed.append({**work, 'authorships': authors})
    reviewed, audit = review_affiliations(typed)
    audit = taxonomy_audit + audit
    output = []
    for work in reviewed:
        doi = re.sub(r'^https?://(?:dx\.)?doi\.org/', '', work.get('doi') or '', flags=re.I).lower()
        decision = DEPARTMENT_AFFILIATION_DECISIONS['overrides'].get(doi)
        if decision:
            original = sorted({i['id'] for a in work['authorships'] for i in a['institutions'] if i.get('type') == 'education'})
            work = {**work, 'authorships': [{'institutions': decision['institutions']}]}
            audit.append({'work_id': work['id'], 'doi': doi, 'decision': 'publisher_verified_work_level_institutions',
                'source': decision['source'], 'original_education_institutions': original,
                'retained_education_institutions': [i['id'] for i in decision['institutions']]})
        output.append(work)
    return output, audit


def validate_config(config):
    start, end = map(int, config['publication_years'].split('-'))
    windows = config['growth_windows']
    if windows != [[start, (start + end) // 2], [(start + end) // 2 + 1, end]]:
        raise ValueError('Two adjacent equal-duration publication windows required')
    if end - start + 1 > 20 or (end - start + 1) % 2:
        raise ValueError('Even publication window of at most twenty years required')
    journals = config['candidate_journals']
    ids = [j['source_id'] for j in journals]
    if not journals or len(ids) != len(set(ids)) or len(journals) > 40:
        raise ValueError('Unique bounded journal source list required')
    return start, end


def calculate(works, config, minimum=50, fractional=True):
    start, end = validate_config(config)
    reviewed, audit = review_department_affiliations(works)
    groups = defaultdict(list)
    allowed_sources = {journal['source_id'] for journal in config['candidate_journals']}
    dois = {}
    ids = set()
    for work in reviewed:
        if work['primary_location']['source']['id'] not in allowed_sources:
            raise ValueError('Work journal is outside configured source set')
        if work['id'] in ids:
            raise ValueError('Duplicate work ID')
        ids.add(work['id'])
        doi = (work.get('doi') or '').strip().lower()
        if doi:
            if doi in dois:
                raise ValueError('Duplicate DOI requires review')
            dois[doi] = work['id']
        groups[(work['primary_location']['source']['id'], work['publication_year'])].append(work)
    if {year for _, year in groups} != set(range(start, end + 1)):
        raise ValueError('Incomplete publication years')
    if {source for source, _ in groups} != allowed_sources:
        raise ValueError('Configured journal is missing from the corpus')
    credits, thresholds = {}, {}
    for (sid, year), cohort in groups.items():
        counts = sorted((w['cited_by_count'] for w in cohort), reverse=True)
        target = len(counts) / 10
        boundary = counts[math.ceil(target) - 1]
        weight = (target - sum(n > boundary for n in counts)) / counts.count(boundary)
        for work in cohort:
            citations = work['cited_by_count']
            credits[work['id']] = 1 if citations > boundary else weight if citations == boundary else 0
        if abs(sum(credits[w['id']] for w in cohort) - target) > 1e-7:
            raise ValueError('Top-decile mass does not reconcile')
        thresholds[f'{sid}:{year}'] = {'works': len(cohort), 'boundary_citations': boundary, 'boundary_credit': weight}
    schools = {}
    missing = 0
    midpoint = config['growth_windows'][0][1]
    for work in reviewed:
        institutions = {i['id']: i for author in work['authorships'] for i in author['institutions'] if i.get('type') == 'education'}
        if not institutions:
            missing += 1
        for iid, institution in institutions.items():
            if iid not in schools:
                schools[iid] = {'institution_id': iid, 'institution': institution['display_name'],
                    'country': institution.get('country_code'), 'articles': 0, 'fractional_articles': 0.,
                    'top_decile_equivalent': 0., 'fractional_citations': 0.,
                    'articles_early': 0, 'articles_recent': 0}
            school = schools[iid]
            fraction = 1 / len(institutions) if fractional else 1
            school['articles'] += 1
            school['fractional_articles'] += fraction
            school['top_decile_equivalent'] += credits[work['id']] * fraction
            school['fractional_citations'] += work['cited_by_count'] * fraction
            school['articles_early' if work['publication_year'] <= midpoint else 'articles_recent'] += 1
    eligible = sorted((s for s in schools.values() if s['articles'] >= minimum),
        key=lambda s: (-round(s['top_decile_equivalent'], 8), -round(s['fractional_citations'], 8), s['institution_id']))
    previous, rank = None, 0
    for position, school in enumerate(eligible, 1):
        score = (round(school['top_decile_equivalent'], 8), round(school['fractional_citations'], 8))
        if score != previous:
            rank = position
        school['rank'] = rank
        previous = score
        school['top_decile_share_pct'] = 100 * school['top_decile_equivalent'] / school['fractional_articles']
        school['output_change'] = school['articles_recent'] - school['articles_early']
        school['output_change_pct'] = 100 * school['output_change'] / school['articles_early'] if school['articles_early'] else None
    return eligible, {'works': len(reviewed), 'without_education_affiliation': missing,
        'institution_entities': len(schools), 'eligible_institutions': len(eligible),
        'minimum_articles': minimum, 'fractional_institution_credit': fractional,
        'journal_year_thresholds': thresholds, 'affiliation_decisions': len(audit)}, reviewed, audit


def sensitivity(works, config, base):
    scenarios = {}
    for minimum in [25, 100]:
        rows, _, _, _ = calculate(works, config, minimum=minimum)
        scenarios['minimum_' + str(minimum)] = rows
    scenarios['whole_institution_credit'] = calculate(works, config, fractional=False)[0]
    for journal in config['candidate_journals']:
        subset = [w for w in works if w['primary_location']['source']['id'] != journal['source_id']]
        scenario_config = {**config, 'candidate_journals': [j for j in config['candidate_journals'] if j['source_id'] != journal['source_id']]}
        scenarios['without_' + journal['source_id'].rsplit('/', 1)[-1]] = calculate(subset, scenario_config)[0]
    return {name: {'eligible_institutions': len(rows), 'base_top20_positions': [
        {'institution_id': s['institution_id'], 'institution': s['institution'], 'base_rank': s['rank'],
         'scenario_rank': next((r['rank'] for r in rows if r['institution_id'] == s['institution_id']), None)}
        for s in base[:20]]} for name, rows in scenarios.items()}


def main():
    global AFFILIATION_RULES, DEPARTMENT_AFFILIATION_DECISIONS
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data_dir',type=Path)
    args=parser.parse_args()
    root=args.data_dir.resolve()
    AFFILIATION_RULES=json.loads((root/'affiliation-rules.json').read_text(encoding='utf-8'))
    decision_path=root/'department-affiliation-decisions.json'
    if decision_path.exists():DEPARTMENT_AFFILIATION_DECISIONS=json.loads(decision_path.read_text(encoding='utf-8'))
    config=json.loads((root/'study.json').read_text(encoding='utf-8'))
    works=[json.loads(line) for line in (root/'works.jsonl').read_text(encoding='utf-8').splitlines()]
    rows,coverage,_,_=calculate(works,config)
    with (root/'reproduced-schools.csv').open('w',encoding='utf-8',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    variants=sensitivity(works,config,rows)
    (root/'reproduced-sensitivity.json').write_text(json.dumps(variants,sort_keys=True),encoding='utf-8')
    expected=list(csv.DictReader((root/'schools.csv').open(encoding='utf-8',newline='')))
    if len(expected)!=len(rows):raise ValueError('Institution count mismatch')
    for before,after in zip(expected,rows):
        for key,value in before.items():
            actual=after[key]
            if isinstance(actual,(int,float)):
                if not value or abs(float(value)-actual)>1e-8:raise ValueError('Numerical mismatch: '+key)
            elif value != ('' if actual is None else str(actual)):
                raise ValueError('Identity mismatch: '+key)
    if variants!=json.loads((root/'sensitivity.json').read_text(encoding='utf-8')):
        raise ValueError('Sensitivity mismatch')
    print(json.dumps({'articles':len(works),'institutions':len(rows),'reproduction':'verified'}))


if __name__=='__main__':main()
