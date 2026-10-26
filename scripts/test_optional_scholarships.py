"""Offline eligibility-tier calculations; no network, credentials or personalized awards.

Calculation/check mode uses only Python's standard library. Rendering imports the
shared PrepSavvy theme and matplotlib. The separate 47-row Alabama study is untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / 'data/test-optional-scholarships/2026-10-27'
DEFAULT_OUTPUT = ROOT / 'figures/test-optional-scholarships/2026-10-27'


def load_bundle(directory=DEFAULT_DATA):
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
    for filename, digest in manifest['files'].items():
        if Path(filename).name != filename or hashlib.sha256((directory / filename).read_bytes()).hexdigest() != digest:
            raise ValueError('Frozen file checksum/path mismatch')
    bundle = json.loads((directory / 'merit.json').read_text(encoding='utf-8'))
    validate_rows(bundle['offers'])
    if manifest['eligibility_routes'] != 16 or manifest['published_tiers'] != 9 or manifest['sources'] != bundle['sources']:
        raise ValueError('Manifest scope/source mismatch')
    return bundle, manifest


def validate_rows(rows):
    if len(rows) != 16 or len({r['record_id'] for r in rows}) != 16:
        raise ValueError('Expected sixteen unique alternative routes')
    if {r['institution_id'] for r in rows} != {'uky', 'eku'} or len({r['tier_id'] for r in rows}) != 9:
        raise ValueError('Unexpected institution/tier scope')
    if any(r['entry_year'] != 2027 or r['entry_term'] != 'fall' for r in rows):
        raise ValueError('Incompatible entry cohort')
    seen = set()
    for r in rows:
        signature = (r['institution_id'], r['tier_id'], r['exam'])
        if signature in seen:
            raise ValueError('Duplicate tier/exam route')
        seen.add(signature)
        if r['route_semantics'] != 'alternative_minimum_eligibility_not_additive':
            raise ValueError('Unsupported route semantics')
        if r['award_kind'] != 'cash' or r['annual_amount_min'] != r['annual_amount_max']:
            raise ValueError('Unpriced package/range cannot be a fixed annual tier')
        if not 0 <= r['gpa_min'] <= 4 or (r['gpa_max'] is not None and not r['gpa_min'] <= r['gpa_max'] <= 4):
            raise ValueError('Invalid GPA band')
        if r['exam'] == 'NONE':
            if r['score_min'] is not None or r['score_max'] is not None:
                raise ValueError('No-test route contains score requirement')
        else:
            low, high = {'ACT': (1, 36), 'SAT': (400, 1600)}[r['exam']]
            if not low <= r['score_min'] <= r['score_max'] <= high:
                raise ValueError('Invalid exam bounds')
        if r['citizenship_rule'] is not None:
            raise ValueError('Frozen sources do not establish a citizenship rule')


def routes_at(rows, institution, gpa, score=None, exam='ACT', include_no_test=False):
    """Match academic conditions only. Residency/other eligibility is not evaluated."""
    if institution not in {'uky', 'eku'} or not 0 <= gpa <= 4:
        raise ValueError('Unknown institution or invalid unweighted GPA')
    if exam not in {'ACT', 'SAT', 'NONE'}:
        raise ValueError('Unknown exam')
    if exam != 'NONE':
        low, high = {'ACT': (1, 36), 'SAT': (400, 1600)}[exam]
        if score is None or isinstance(score, bool) or int(score) != score or not low <= score <= high:
            raise ValueError('Invalid/missing exam score')
    elif score is not None:
        raise ValueError('No-test route must not contain a score')
    result = []
    for r in rows:
        if r['institution_id'] != institution or not r['gpa_min'] <= gpa or (r['gpa_max'] is not None and gpa > r['gpa_max']):
            continue
        if r['exam'] == 'NONE' and (exam == 'NONE' or include_no_test):
            result.append(r)
        elif r['exam'] == exam and exam != 'NONE' and r['score_min'] <= score <= r['score_max']:
            result.append(r)
    if not result:
        raise LookupError('No published qualifying route; this is not a zero-dollar award')
    return result


def highest_tier(rows, institution, gpa, score=None, exam='ACT', include_no_test=False):
    matches = routes_at(rows, institution, gpa, score, exam, include_no_test)
    maximum = max(r['annual_amount_min'] for r in matches)
    winners = [r for r in matches if r['annual_amount_min'] == maximum]
    if len({r['tier_id'] for r in winners}) != 1:
        raise ValueError('Ambiguous equal-value tiers require manual review')
    return {'annual_usd': maximum, 'tier_id': winners[0]['tier_id'], 'record_ids': sorted(r['record_id'] for r in winners)}


def calculate(bundle):
    rows = bundle['offers']
    panels = []
    for school, gpa, before, after, expected, label in [
        ('uky', 3.5, 29, 30, (13000, 16000), 'UKY Bluegrass | Nonresident | Unweighted GPA 3.50'),
        ('eku', 3.8, 27, 28, (7000, 9000), 'Eastern Kentucky | Kentucky resident, on campus | Unweighted GPA 3.80'),
    ]:
        steps = [{'act': score, **highest_tier(rows, school, gpa, score, include_no_test=True)} for score in range(26, 33)]
        low = highest_tier(rows, school, gpa, before, include_no_test=True)['annual_usd']
        high = highest_tier(rows, school, gpa, after, include_no_test=True)['annual_usd']
        if (low, high) != expected:
            raise ValueError('Frozen evidence no longer reproduces reviewed threshold')
        panels.append({'institution_id': school, 'unweighted_gpa': gpa, 'label': label, 'before_act': before, 'after_act': after, 'before_annual_usd': low, 'after_annual_usd': high, 'increase_annual_usd': high-low, 'steps': steps})
    no_test = sorted([{'gpa_min': r['gpa_min'], 'annual_usd': r['annual_amount_min'], 'record_id': r['record_id']} for r in rows if r['institution_id'] == 'uky' and r['exam'] == 'NONE'], key=lambda r:r['gpa_min'])
    if [(r['gpa_min'], r['annual_usd']) for r in no_test] != [(3,6500),(3.5,10000),(3.6,13000),(3.8,16000)]:
        raise ValueError('UKY no-test tiers differ from reviewed evidence')
    return {'edition': '2026-10-27', 'source_acquisition_date': '2026-10-26', 'entry': 'fall 2027', 'route_count': len(rows), 'tier_count': len({r['tier_id'] for r in rows}), 'panels': panels, 'uky_no_test': no_test, 'uky_16000_traditional': {'gpa_min': 3.5, 'act_min': 30, 'sat_min': 1360, 'annual_usd': 16000}, 'interpretation': 'Highest published qualifying tier among academic routes, including no-test alternatives. Awards are not summed; eligibility and limited funds remain separate. Not a personalized aid offer.'}


def render(result, output=DEFAULT_OUTPUT):
    from chart_theme import BLUE, GREEN, GRID, canvas, save
    from matplotlib.ticker import FuncFormatter
    output = Path(output)
    money = FuncFormatter(lambda value, _: f'${value/1000:g}k')
    fig, ax = canvas('Where an ACT point changes a test-optional award tier',
        'Published annual tiers for fall 2027. Each panel keeps its own residency and unweighted GPA conditions.', height=8.0, left=.11)
    ax.remove()
    for data, y in zip(result['panels'], [.59, .26]):
        ax = fig.add_axes([.11, y, .84, .22])
        x = [r['act'] for r in data['steps']]
        awards = [r['annual_usd'] for r in data['steps']]
        ax.step(x, awards, where='post', color=BLUE, lw=2.5)
        ax.plot([data['after_act']]*2, [data['before_annual_usd'], data['after_annual_usd']], color=GREEN, lw=4)
        ax.scatter([data['before_act'],data['after_act']], [data['before_annual_usd'],data['after_annual_usd']], c=[BLUE,GREEN], s=50,zorder=5)
        ax.text(0,1.13,data['label'],transform=ax.transAxes,fontsize=9,weight='bold',va='top',bbox={'facecolor':'white','edgecolor':'none','pad':2})
        ax.text(.04,.90,f"ACT {data['before_act']} to {data['after_act']}: +${data['increase_annual_usd']:,} annually",transform=ax.transAxes,color=GREEN,weight='bold',fontsize=10)
        ax.set_xlim(25.7,32.3)
        ax.set_ylim(0,18000)
        ax.set_xticks(range(26,33))
        ax.set_yticks([0,5000,10000,15000])
        ax.yaxis.set_major_formatter(money)
        ax.grid(axis='y',color=GRID)
        ax.set_xlabel('ACT composite (no superscore)')
        ax.spines['bottom'].set_color('#BFBFBF')
    fig.text(.025,.12,'EKU below ACT 28 uses the no-test President\u2019s route. UKY: automatic consideration, not guaranteed aid.\nBoth: limited funds and additional eligibility. Panels do not compare college net prices.',fontsize=8)
    save(fig,output,'act-tier-changes','Sources: UKY fall 2027; EKU 2027\u201328 grid and linked terms. Acquired 26 Oct 2026.')
    fig, ax = canvas('At UKY, GPA can reach the same tier without a test',
        'Nonresident Bluegrass: four published test-optional tiers, plus the ACT route to $16,000 annually.',height=5.8,left=.11)
    fig.subplots_adjust(bottom=.26)
    points = result['uky_no_test']
    xs = [r['gpa_min'] for r in points] + [4.0]
    ys = [r['annual_usd'] for r in points] + [points[-1]['annual_usd']]
    ax.step(xs,ys,where='post',color=BLUE,lw=3,label='No-test GPA route')
    ax.scatter(xs[:-1],ys[:-1],color=BLUE,s=40,zorder=4)
    ax.plot([3.5,4.0],[16000,16000],color=GREEN,lw=2,ls='--',label='Traditional route: ACT 30+ and GPA 3.50+')
    ax.scatter([3.5],[16000],color=GREEN,s=60,zorder=5)
    for x,y in zip(xs[:-1],ys[:-1]):
        ax.annotate(f'${y:,}',(x,y),xytext=(7,-17 if y==16000 else 8),textcoords='offset points',fontsize=9,bbox={'facecolor':'white','edgecolor':'none','pad':1})
    ax.text(3.52,17100,'ACT 30 + GPA 3.50 reaches the $16,000 tier',fontsize=9,color=GREEN,weight='bold')
    ax.set_xlim(2.98,4.02)
    ax.set_ylim(0,19000)
    ax.set_xticks([3.0,3.2,3.4,3.5,3.6,3.8,4.0])
    ax.set_yticks([0,5000,10000,15000])
    ax.yaxis.set_major_formatter(money)
    ax.set_xlabel('Unweighted high-school GPA')
    ax.legend(loc='lower right',frameon=False,fontsize=8)
    fig.text(.025,.105,'At GPA 3.80, the no-test route already reaches $16,000. Published criteria establish consideration;\nUKY awards remain subject to admission, application timing, available funds and individual terms.',fontsize=8)
    save(fig,output,'uky-no-test-gpa-tiers','Source: University of Kentucky fall-2027 scholarship page. Acquired 26 Oct 2026.')
    for path in output.glob('*.svg'):
        path.write_text('\n'.join(line.rstrip() for line in path.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,default=DEFAULT_DATA)
    parser.add_argument('--output',type=Path,default=DEFAULT_OUTPUT)
    parser.add_argument('--render',action='store_true')
    args = parser.parse_args()
    bundle,_ = load_bundle(args.data)
    result = calculate(bundle)
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'chart-inputs.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    if args.render:
        render(result,args.output)
    print(json.dumps({'route_count':result['route_count'],'tier_count':result['tier_count'],'annual_increases':[p['increase_annual_usd'] for p in result['panels']]}))


if __name__ == '__main__':
    main()
