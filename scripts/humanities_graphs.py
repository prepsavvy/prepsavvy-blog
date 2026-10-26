"""Render the humanities story's charts from independently recalculated data."""
import argparse
import csv
import json
from pathlib import Path
from matplotlib.ticker import PercentFormatter
from chart_theme import BLUE, GREEN, GRID, canvas, save
from humanities_growth import calculate


def render(data, output):
    manifest=json.loads((data/'manifest.json').read_text())
    with (data/'program-awards.csv').open(encoding='utf-8',newline='') as f:
        result=calculate(list(csv.DictReader(f)),manifest['years'])
    a,b=manifest['years']
    source=f'Source: NCES IPEDS. First-major bachelor awards, {a} and {b}. Selected humanities subjects.'
    national=result['national']
    fig,ax=canvas('Humanities degrees fell faster than the national total',
        f'U.S. awards, indexed to {a} = 100; only the two observed years are shown',4.8,.24)
    for y,(field,label) in enumerate([('humanities_awards','Selected humanities'),('bachelor_awards',"All bachelor's awards")]):
        x,z=national[0][field],national[1][field]
        end=100*z/x
        ax.plot([end,100],[y,y],color=BLUE,lw=4)
        ax.scatter([100],[y],s=65,facecolor='white',edgecolor=BLUE,zorder=3)
        ax.scatter([end],[y],s=65,color=BLUE,zorder=3)
        ax.text(end-1,y,f'{end-100:.1f}%',ha='right',va='center',weight='bold',color=BLUE)
        ax.text(103,y,f'{x:,} → {z:,}',ha='left',va='center',fontsize=11)
    ax.set_yticks([0,1],['Selected humanities',"All bachelor's awards"])
    ax.set_xlim(76,116)
    ax.set_ylim(-.6,1.6)
    ax.set_xticks([80,90,100])
    ax.set_xlabel(f'Award count index ({a} = 100)')
    save(fig,output,'national-decline',source)

    names={'110510':'CSU San Bernardino','122409':'San Diego State','220978':'Middle Tennessee State'}
    subjects=['English and writing','History','Languages and linguistics','Philosophy and religious studies','Humanistic studies']
    short=['English and writing','History','Languages','Philosophy / religion','Humanistic studies']
    fig,base=canvas('English and history drove the growth at three public universities',
        f'Change in bachelor awards by subject, {a} to {b}; all included subjects are shown',6.3,.26)
    base.remove()
    for i,(unit,name) in enumerate(names.items()):
        ax=fig.add_axes([.26+i*.235,.20,.205,.59])
        rows={r['subject']:r for r in result['institution_subjects'] if r['unitid']==unit}
        changes=[rows[s]['change_awards'] for s in subjects]
        bars=ax.barh(range(5),changes,color=[GREEN if n>=0 else BLUE for n in changes],height=.55)
        ax.bar_label(bars,labels=[f'{n:+d}' if n else '0' for n in changes],padding=4,fontsize=10)
        ax.set_title(name,fontsize=10,pad=13,weight='bold')
        ax.set_yticks(range(5),short if i==0 else ['']*5)
        ax.invert_yaxis()
        ax.set_xlim(-16,62)
        ax.set_xticks([0,25,50])
        ax.axvline(0,color='#8C8C8C',lw=.8)
        ax.xaxis.grid(True,color=GRID)
        ax.set_axisbelow(True)
        ax.tick_params(length=0,pad=6)
        ax.spines['bottom'].set_visible(False)
    fig.text(.26,.105,'Additional awards. Green: increase. Blue: decrease.',fontsize=9)
    save(fig,output,'subject-growth',source)

    focus=[next(r for r in result['institutions'] if r['unitid']==u) for u in ['110510','122409','220978','130794']]
    fig,ax=canvas('A bigger graduating class does not always mean a bigger share',
        f'Humanities as a share of all bachelor awards, {a} → {b}',5.4,.26)
    for y,r in enumerate(focus[::-1]):
        x,z=r['baseline_share_pct'],r['latest_share_pct']
        color=GREEN if z>x else BLUE
        ax.plot([x,z],[y,y],color=color,lw=4)
        ax.scatter(x,y,s=55,facecolor='white',edgecolor=color,zorder=3)
        ax.scatter(z,y,s=55,color=color,zorder=3)
        ax.text(max(x,z)+.45,y,f'{x:.1f}% → {z:.1f}%',va='center',fontsize=10)
    ax.set_yticks(range(4),[names.get(r['unitid'],'Yale') for r in focus[::-1]])
    ax.set_xlim(0,19)
    ax.set_ylim(-.6,3.6)
    ax.set_xticks([0,5,10,15])
    ax.xaxis.set_major_formatter(PercentFormatter(100,decimals=0))
    ax.set_xlabel('Share of all bachelor awards')
    save(fig,output,'humanities-share',source)
    print(json.dumps({'state':'rendered','figures':3,'formats':['PNG','SVG'],'output':str(output)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    render(args.data,args.output)
