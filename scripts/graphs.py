"""Render publication figures from the frozen PrepSavvy research release."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / '2026-10-23'
OUT = ROOT / 'figures' / '2026-10-23'
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':11,
                     'svg.hashsalt':'prepsavvy-philosophy-2026-10-23'})
rows = list(csv.DictReader((DATA/'schools.csv').open(encoding='utf-8')))
short = {'University of California, Irvine':'UC Irvine',
         'Rutgers, The State University of New Jersey':'Rutgers',
         'Massachusetts Institute of Technology':'MIT',
         'University of Southern California':'USC'}
def label(r):
    return short.get(r['institution'], r['institution'].replace('University of ',''))
def save(fig, name, source):
    fig.text(.02,.015,source,fontsize=9,color='#475569')
    for ax in fig.axes:
        ax.spines[['top','right']].set_visible(False)
        ax.set_axisbelow(True)
    fig.savefig(OUT/(name+'.svg'),bbox_inches='tight',metadata={'Date':None})
    fig.savefig(OUT/(name+'.png'),dpi=180,bbox_inches='tight',metadata={'Software':'PrepSavvy'})
    plt.close(fig)

top = rows[:20][::-1]
fig,ax=plt.subplots(figsize=(11,10))
values=[float(r['top_decile_equivalent']) for r in top]
bars=ax.barh([label(r) for r in top],values,color=['#2563eb' if r['country']=='US' else '#64748b' for r in top])
ax.bar_label(bars,labels=[f'{v:.1f}' for v in values],padding=4,fontsize=10)
ax.set_xlim(0,max(values)*1.15)
ax.set_xlabel('Fractional contributions to the most-cited 10% within each journal and year')
ax.set_title('Oxford leads the index; UC Irvine leads U.S. institutions',loc='left',fontweight='bold',pad=18)
fig.text(.02,.055,'31 selected philosophy journals, 2015–2024. Blue bars: U.S. institutions.',fontsize=10)
fig.subplots_adjust(left=.31,bottom=.13,top=.92)
save(fig,'research-influence','Source: PrepSavvy analysis of OpenAlex. Snapshot: 23 October 2026. Full table and method in repository.')

selected=[r for r in rows if r['institution'] in ['Princeton University','University of California, Irvine','University of Southern California','New York University','Rutgers, The State University of New Jersey']]
selected.sort(key=lambda r:float(r['output_change_pct']))
fig,ax=plt.subplots(figsize=(10,5))
growth=[float(r['output_change_pct']) for r in selected]
bars=ax.barh([label(r) for r in selected],growth,color=['#2563eb' if v>=0 else '#b45309' for v in growth])
for bar,v in zip(bars,growth):
    ax.text(v+(2 if v>=0 else -2),bar.get_y()+bar.get_height()/2,f'{v:+.1f}%',ha='left' if v>=0 else 'right',va='center')
ax.axvline(0,color='#475569',linewidth=.8)
ax.set_xlim(-50,140)
ax.set_xlabel('Change in indexed article count: 2015–2019 versus 2020–2024 (%)')
ax.set_title('Princeton and UC Irvine gained publication momentum',loc='left',fontweight='bold',pad=18)
fig.subplots_adjust(left=.22,bottom=.20,top=.85)
save(fig,'publication-growth','Source: PrepSavvy / OpenAlex. Selected U.S. institutions from the top 20; fixed journal coverage, not faculty headcounts.')

programs=list(csv.DictReader((DATA/'program-years.csv').open(encoding='utf-8')))
fig,axes=plt.subplots(1,2,figsize=(12,5),sharex=True)
for unitid,name,style in [('110653','UC Irvine','-'),('186131','Princeton','--'),('123961','USC',':')]:
    for ax,level,caption in zip(axes,[5,17],['Bachelor’s degrees awarded','Research doctorates awarded']):
        values=[]
        for year in range(2018,2025):
            found=[int(p['awards']) for p in programs if p['unitid']==unitid and int(p['year'])==year and int(p['award_level'])==level]
            values.append(sum(found) if found else float('nan'))
        ax.plot(range(2018,2025),values,style,marker='o',label=name,linewidth=2)
        ax.set_title(caption,loc='left')
        ax.set_ylabel('First-major awards, CIP family 38.01')
        ax.set_xticks([2018,2020,2022,2024])
for ax in axes:
    ax.set_ylim(bottom=0)
axes[0].legend(frameon=False)
fig.suptitle('Research influence and degree output describe different strengths',x=.02,ha='left',fontweight='bold')
fig.subplots_adjust(bottom=.20,top=.82,wspace=.25)
save(fig,'degree-trends','Source: NCES IPEDS revised releases, 2018–2024. Philosophy, logic, ethics and related philosophy codes; first majors only.')
print('Generated 3 figures in SVG and PNG')
