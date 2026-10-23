"""Reproduce four philosophy research charts using PrepSavvy's canonical style."""
import csv,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import PercentFormatter
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'2026-10-23'; OUT=ROOT/'figures'/'2026-10-23'
for font in (ROOT/'assets'/'fonts').glob('*.ttf'):font_manager.fontManager.addfont(str(font))
STYLE=json.loads((ROOT/'assets'/'chart-style.json').read_text())
BLUE=STYLE['primary'];INK=STYLE['text'];GREY=STYLE['neutral'];GRID=STYLE['grid']
plt.rcParams.update({'font.family':'Manrope','font.size':11,'text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'prepsavvy-philosophy-v2','svg.fonttype':'path'})
rows=list(csv.DictReader((DATA/'schools.csv').open(encoding='utf-8')))
for r in rows:
 for k in ['top_decile_equivalent','top_decile_share_pct','output_change_pct']:r[k]=float(r[k])
 for k in ['rank','articles','articles_2015_2019','articles_2020_2024']:r[k]=int(r[k])
SHORT={'University of California, Irvine':'UC Irvine','Rutgers, The State University of New Jersey':'Rutgers','Massachusetts Institute of Technology':'MIT','University of Southern California':'USC','Australian National University':'ANU','Ruhr University Bochum':'Ruhr Bochum','New York University':'NYU','Princeton University':'Princeton'}
def label(r):return SHORT.get(r['institution'],r['institution'].replace('University of ',''))
def canvas(title,subtitle,height=6,left=.24):
 fig,ax=plt.subplots(figsize=(11,height),facecolor='white')
 fig.text(.025,.96,title,fontsize=18,fontweight='bold',va='top');fig.text(.025,.90,subtitle,fontsize=11,va='top')
 fig.text(.025,.035,'PREPSAVVY RESEARCH',color=BLUE,fontsize=10,fontweight='bold');fig.text(.975,.035,'OpenAlex · 23 Oct 2026',ha='right',fontsize=9)
 fig.subplots_adjust(left=left,right=.92,bottom=.23,top=.80)
 ax.spines[['left','bottom']].set_color('#BFBFBF');ax.set_axisbelow(True);ax.tick_params(length=0,pad=8)
 return fig,ax

def save(fig,name):
 fig.savefig(OUT/(name+'.svg'),metadata={'Date':None});fig.savefig(OUT/(name+'.png'),dpi=180,metadata={'Software':'PrepSavvy'});plt.close(fig)

top=rows[:10][::-1]
fig,ax=canvas('Oxford leads; UC Irvine is the strongest U.S. contributor','Influence in 31 selected philosophy journals, 2015–2024',7.2)
bars=ax.barh([label(r) for r in top],[r['top_decile_equivalent'] for r in top],color=[BLUE if r['country']=='US' else GREY for r in top],height=.60,zorder=2)
ax.bar_label(bars,labels=[f"{r['top_decile_equivalent']:.1f}" for r in top],padding=7,fontweight='bold')
ax.set_xlim(0,90);ax.xaxis.grid(True,color=GRID);ax.set_xlabel('Highly cited article contributions, with shared institutional credit',labelpad=12)
fig.text(.025,.085,'Blue identifies U.S. institutions. The article table contains the full top 20.',fontsize=9)
save(fig,'research-influence-v2')

top=sorted(rows[:20],key=lambda r:r['output_change_pct'])
fig,ax=canvas('Fourteen of the top twenty increased their research output','Every institution in the top 20, ordered by publication growth',10.4,.28)
for y,r in enumerate(top):
 a=r['articles_2015_2019'];b=r['articles_2020_2024']
 ax.plot([a,b],[y,y],color=BLUE if b>a else GREY,linewidth=2,zorder=2)
 ax.scatter(a,y,s=42,facecolors='white',edgecolors=INK,zorder=3);ax.scatter(b,y,s=42,color=BLUE if b>a else INK,zorder=3)
 ax.text(max(a,b)+8,y,f"{a} → {b}  ({r['output_change_pct']:+.0f}%)",va='center',fontsize=9)
ax.set_yticks(range(len(top)),[label(r) for r in top]);ax.set_xlim(0,470);ax.set_xticks([0,100,200,300]);ax.xaxis.grid(True,color=GRID);ax.set_xlabel('Indexed articles per five-year period',labelpad=12)
fig.text(.025,.085,'Open circles: 2015–2019. Filled circles: 2020–2024. Counts use the same journals.',fontsize=9)
save(fig,'research-momentum')

eligible=sorted([r for r in rows if r['articles']>=100],key=lambda r:-r['top_decile_share_pct'])
top=(eligible[:10]+[r for r in eligible[10:] if label(r)=='Oxford'])[::-1]
fig,ax=canvas('UC Irvine has the highest concentration of highly cited work','Among institutions with at least 100 indexed articles; Oxford is shown for comparison',7.6)
bars=ax.barh([label(r) for r in top],[r['top_decile_share_pct'] for r in top],color=[BLUE if label(r)=='UC Irvine' else GREY for r in top],height=.60,zorder=2)
ax.bar_label(bars,labels=[f"{r['top_decile_share_pct']:.1f}%" for r in top],padding=7,fontweight='bold')
ax.axvline(10,color=INK,linewidth=1,linestyle='--');ax.set_xlim(0,26);ax.xaxis.set_major_formatter(PercentFormatter(100,decimals=0));ax.xaxis.grid(True,color=GRID);ax.set_xlabel('Highly cited share of institutionally attributed output',labelpad=12)
fig.text(.025,.085,'Institutional credit is fractional. Dashed line: the 10% journal/year reference.',fontsize=9)
save(fig,'research-concentration')

fig,ax=canvas('Influential research communities are not all expanding','All 112 eligible institutions: research influence against change in publication volume',7,.11)
ax.scatter([r['output_change_pct'] for r in rows],[r['top_decile_equivalent'] for r in rows],color=GREY,s=28,alpha=.65,edgecolors='white',linewidth=.5)
offsets={'Oxford':(8,-2),'UC Irvine':(8,4),'NYU':(-36,8),'Princeton':(8,5),'Ruhr Bochum':(10,-12),'Edinburgh':(-74,4)}
for r in rows:
 name=label(r)
 if name in offsets:
  ax.scatter(r['output_change_pct'],r['top_decile_equivalent'],s=42,color=BLUE,zorder=3);ax.annotate(name,(r['output_change_pct'],r['top_decile_equivalent']),xytext=offsets[name],textcoords='offset points',fontsize=10,fontweight='bold')
ax.axvline(0,color=INK,linestyle='--',linewidth=1);ax.set_xlabel('Publication growth: 2015–2019 to 2020–2024',labelpad=12);ax.xaxis.set_major_formatter(PercentFormatter(100,decimals=0));ax.set_ylabel('Research influence score',labelpad=12);ax.set_ylim(0,90);ax.yaxis.grid(True,color=GRID)
fig.text(.025,.085,'Each dot is an institution. Growth measures article output, not faculty or enrollment.',fontsize=9)
save(fig,'influence-and-growth')
print('Generated four branded figures in PNG and SVG')
