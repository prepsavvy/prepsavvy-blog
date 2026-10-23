import csv, json, math, hashlib, re, unicodedata
from collections import defaultdict
from pathlib import Path
AFFILIATION_RULES=json.loads(Path('affiliation-rules.json').read_text(encoding='utf-8'))

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

def calculate(works,minimum=50):
    """Use fractional allocation at a citation tie boundary, conserving 10% mass.

    Full output counts are shown alongside fractional counts. Missing affiliation
    is visible in coverage. All education-type affiliations split each paper's
    institutional credit equally. No current-faculty attribution is inferred.
    """
    works,_=review_affiliations(works)
    by_year=defaultdict(list)
    for w in works:
        journal=w['primary_location']['source']['id']
        by_year[(journal,w['publication_year'])].append(w)
    if {year for _,year in by_year}!=set(range(2015,2025)):raise ValueError('Incomplete publication years')
    credits={};thresholds={}
    for (journal,year),cohort in by_year.items():
        ordered=sorted(w['cited_by_count'] for w in cohort)[::-1]
        target=len(ordered)/10
        boundary=ordered[math.ceil(target)-1]
        above=sum(c>boundary for c in ordered);tied=ordered.count(boundary)
        weight=(target-above)/tied
        thresholds[f'{journal}:{year}']={'works':len(cohort),'boundary_citations':boundary,'boundary_credit':weight}
        for w in cohort:
            n=w['cited_by_count'];credits[w['id']]=1 if n>boundary else weight if n==boundary else 0
        if abs(sum(credits[w['id']] for w in cohort)-target)>1e-7:
            raise ValueError('Top-decile credit does not reconcile')
    schools={};unaffiliated=0;duplicate_dois=defaultdict(list)
    for w in works:
        if w.get('doi'):duplicate_dois[w['doi'].lower()].append(w['id'])
        institutions={i['id']:i for a in w['authorships'] for i in a['institutions'] if i.get('type')=='education'}
        if not institutions:unaffiliated+=1
        for iid,i in institutions.items():
            if iid not in schools:
                schools[iid]={'institution_id':iid,'institution':i['display_name'],'country':i.get('country_code'),
                  'articles':0,'fractional_articles':0.,'top_decile_equivalent':0.,'fractional_citations':0.,
                  'articles_2015_2019':0,'articles_2020_2024':0,'top_work_ids':[]}
            s=schools[iid];fraction=1/len(institutions)
            s['articles']+=1;s['fractional_articles']+=fraction
            s['top_decile_equivalent']+=credits[w['id']]*fraction
            s['fractional_citations']+=w['cited_by_count']*fraction
            s['articles_2015_2019' if w['publication_year']<2020 else 'articles_2020_2024']+=1
            s['top_work_ids'].append((w['cited_by_count'],w['id']))
    duplicates={k:v for k,v in duplicate_dois.items() if len(v)>1}
    if duplicates:raise ValueError(f'Duplicate DOI records require review: {len(duplicates)}')
    eligible=[s for s in schools.values() if s['articles']>=minimum]
    eligible.sort(key=lambda s:(-round(s['top_decile_equivalent'],8),-round(s['fractional_citations'],8),s['institution_id']))
    previous=None;rank=0
    for position,s in enumerate(eligible,1):
        score=(round(s['top_decile_equivalent'],8),round(s['fractional_citations'],8))
        if score!=previous:rank=position
        previous=score;s['rank']=rank
        s['top_decile_share_pct']=100*s['top_decile_equivalent']/s['fractional_articles']
        old=s['articles_2015_2019'];s['output_change_pct']=100*(s['articles_2020_2024']/old-1) if old else None
        s['top_work_ids']=[w for _,w in sorted(s['top_work_ids'],reverse=True)[:10]]
    return eligible,{'works':len(works),'without_education_affiliation':unaffiliated,
                     'institution_entities':len(schools),'eligible_institutions':len(eligible),
                     'minimum_articles':minimum,'journal_year_thresholds':thresholds,'duplicate_dois':len(duplicates)}

def period_average(series,start,end):
    selected=[series.get(y) for y in range(start,end+1)]
    return sum(selected)/len(selected) if all(v is not None for v in selected) else None

def combine(rankings,programs,crosswalk):
    by_unit=defaultdict(dict)
    for p in programs:
        key=(p['unitid'],p['award_level'])
        if p['year'] in by_unit[key]:raise ValueError('Duplicate program year')
        by_unit[key][p['year']]=p['awards']
    matrix=[]
    for s in rankings:
        iid=s['institution_id'].rsplit('/',1)[-1]
        mapping=crosswalk.get(iid,[])
        units=mapping.get('unitids',[]) if isinstance(mapping,dict) else mapping
        r={k:v for k,v in s.items() if k!='top_work_ids'}
        r['ipeds_unitids']='|'.join(units)
        r['degree_scope']='CIP 38.01 family; first majors; degree awards, not enrollment'
        r['mapping_note']='Primary campus' if units else 'Not joined'
        if iid=='I102322142':r['mapping_note']='Rutgers bachelor awards aggregate Camden, New Brunswick and Newark; doctorate awards are New Brunswick'
        if iid=='I201448701':r['mapping_note']='Seattle-campus awards; university-wide research entity'
        for level,label in [(5,'bachelors'),(17,'doctorates')]:
            level_units=mapping.get('doctorate_unitids',units) if level==17 and isinstance(mapping,dict) else units
            r[label+'_unitids']='|'.join(level_units)
            series={}
            for y in range(2018,2025):
                values=[by_unit[(uid,level)].get(y) for uid in level_units]
                # Missing is unknown, never silently converted to zero.
                series[y]=sum(values) if values and all(v is not None for v in values) else None
            r[label+'_2024']=series[2024]
            r[label+'_avg_2018_2020']=period_average(series,2018,2020)
            r[label+'_avg_2022_2024']=period_average(series,2022,2024)
            a=r[label+'_avg_2018_2020'];b=r[label+'_avg_2022_2024']
            r[label+'_change_pct']=100*(b/a-1) if a and b is not None else None
        matrix.append(r)
    return matrix

def sensitivity(works,base):
    results={}
    for name,excluded in [
      ('without_technology_journals',{'1388-1957','2210-5433'}),
      ('without_synthese',{'0039-7857'}),
    ]:
        remaining=[w for w in works if w['primary_location']['source'].get('issn_l') not in excluded]
        if len(remaining)==len(works):raise ValueError('Sensitivity exclusion matched no journal')
        schools,_=calculate(remaining)
        ranks={s['institution_id']:s['rank'] for s in schools}
        results[name]={'works':len(remaining),'excluded_issn':sorted(excluded),
          'base_top20_positions':[{'institution':s['institution'],'base_rank':s['rank'],
                                  'scenario_rank':ranks.get(s['institution_id'])} for s in base[:20]]}
    return results

if __name__=='__main__':
    works=[json.loads(line) for line in Path('works.jsonl').read_text(encoding='utf-8').splitlines()]
    schools,coverage=calculate(works)
    with Path('reproduced-rankings.csv').open('w',encoding='utf-8',newline='') as f:
        fields=[k for k in schools[0] if k!='top_work_ids']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        writer.writerows({k:v for k,v in s.items() if k in fields} for s in schools)
    programs=list(csv.DictReader(Path('program-years.csv').open(encoding='utf-8')))
    for p in programs:
        for k in ['year','award_level','awards']:p[k]=int(p[k])
    matrix=combine(schools,programs,json.loads(Path('crosswalk.json').read_text()))
    with Path('reproduced-schools.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(matrix[0]));writer.writeheader();writer.writerows(matrix)
    Path('reproduced-sensitivity.json').write_text(json.dumps(sensitivity(works,schools),indent=2),encoding='utf-8')
    print(json.dumps({'institutions':len(schools),'articles':len(works)}))
