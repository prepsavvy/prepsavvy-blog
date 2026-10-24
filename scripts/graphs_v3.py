"""Reproduce the dictated philosophy chart revision from immutable source data."""
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import PercentFormatter
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from editorial_analysis import nyu_journals

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'figures' / '2026-10-23'
STYLE = json.loads((ROOT / 'assets' / 'chart-style.json').read_text())
BLUE, GRID = STYLE['primary'], STYLE['grid']
GREEN = '#168342'  # PrepSavvy success token: hsl(142 71% 30%).
for font in (ROOT / 'assets' / 'fonts').glob('*.ttf'):
    font_manager.fontManager.addfont(str(font))
plt.rcParams.update({'font.family': 'Manrope', 'font.size': 10,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.spines.left': False, 'svg.hashsalt': 'prepsavvy-philosophy-v3',
    'svg.fonttype': 'path'})
rows = list(csv.DictReader((ROOT / 'data' / '2026-10-23' / 'schools.csv').open(encoding='utf-8')))
for row in rows:
    for k in ['top_decile_equivalent', 'top_decile_share_pct', 'output_change_pct']:
        row[k] = float(row[k])
    for k in ['articles', 'articles_2015_2019', 'articles_2020_2024']:
        row[k] = int(row[k])
SHORT = {'University of California, Irvine': 'UC Irvine', 'New York University': 'NYU',
    'Rutgers, The State University of New Jersey': 'Rutgers', 'Princeton University': 'Princeton',
    'Australian National University': 'ANU', 'Massachusetts Institute of Technology': 'MIT',
    'University of Southern California': 'USC', 'Ruhr University Bochum': 'Ruhr Bochum',
    "King’s College London": "King's College London"}

def name(r):
    return SHORT.get(r['institution'], r['institution'].replace('University of ', ''))

def label(r):
    return name(r)

def flags(ax, institutions):
    # Put each flag after its institution name, directly beside the plotting area.
    ax.tick_params(axis='y', pad=25)
    for y, row in enumerate(institutions):
        flag = plt.imread(ROOT / 'assets/flags' / (row['country'].lower()+'.png'))
        artist = AnnotationBbox(OffsetImage(flag, zoom=.19), (-.027, y),
            xycoords=('axes fraction', 'data'), frameon=False, annotation_clip=False)
        ax.add_artist(artist)

def canvas(title, subtitle, height=6.0, left=.23):
    fig, ax = plt.subplots(figsize=(10, height), facecolor='white')
    fig.text(.025, .975, title, fontsize=16, weight='bold', va='top')
    fig.text(.025, .918, subtitle, fontsize=9, va='top')
    fig.subplots_adjust(left=left, right=.94, bottom=.14, top=.84)
    ax.set_axisbelow(True)
    ax.tick_params(length=0, pad=6)
    ax.spines['bottom'].set_color('#BFBFBF')
    logo = plt.imread(ROOT / 'assets' / 'prepsavvy-logo.png')
    brand = fig.add_axes([.81, .018, .16, .045])
    brand.imshow(logo)
    brand.axis('off')
    return fig, ax

def save(fig, filename):
    fig.savefig(OUT / (filename + '.png'), dpi=180, metadata={'Software': 'PrepSavvy'})
    fig.savefig(OUT / (filename + '.svg'), metadata={'Date': None})
    plt.close(fig)

top = rows[:10][::-1]
fig, ax = canvas('Oxford leads philosophy research influence', 'Highly cited contributions in 31 philosophy journals, 2015–2024')
bars = ax.barh([label(r) for r in top], [r['top_decile_equivalent'] for r in top], color=BLUE, height=.65)
ax.bar_label(bars, labels=[f"{r['top_decile_equivalent']:.1f}" for r in top], padding=5, weight='bold')
ax.set_xlim(0, 84)
ax.xaxis.grid(True, color=GRID)
ax.set_xlabel('Research influence score', labelpad=8)
flags(ax, top)
save(fig, 'research-influence-v5')

eligible = sorted([r for r in rows if r['articles'] >= 100], key=lambda r: -r['top_decile_share_pct'])
top = (eligible[:10] + [r for r in eligible[10:] if name(r) == 'Oxford'])[::-1]
fig, ax = canvas('Irvine produces disproportionately influential work', 'Highly cited share of attributed output; institutions with at least 100 articles', 6.3)
bars = ax.barh([label(r) for r in top], [r['top_decile_share_pct'] for r in top], color=BLUE, height=.65)
ax.bar_label(bars, labels=[f"{r['top_decile_share_pct']:.1f}%" for r in top], padding=5, weight='bold')
ax.axvline(10, color='black', lw=1, ls='--')
ax.set_xlim(0, 24)
ax.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
ax.xaxis.grid(True, color=GRID)
ax.set_xlabel('Highly cited share', labelpad=8)
fig.text(.025, .035, 'Dashed line: 10% journal-year benchmark. Institutional credit is shared.', fontsize=8)
flags(ax, top)
save(fig, 'research-concentration-v5')

top = sorted(rows[:20], key=lambda r: r['output_change_pct'])
fig, ax = canvas('Fourteen of the top twenty increased publication output', 'Articles in 2015–2019 → 2020–2024; ordered by percentage growth', 8.4, .24)
for y, r in enumerate(top):
    a, b = r['articles_2015_2019'], r['articles_2020_2024']
    colour = GREEN if b > a else BLUE
    ax.plot([a, b], [y, y], color=colour, lw=3)
    ax.scatter(a, y, s=30, color='white', edgecolors=colour, zorder=3)
    ax.scatter(b, y, s=30, color=colour, zorder=3)
    ax.text(max(a,b)+5, y, f"{a} → {b} ({r['output_change_pct']:+.0f}%)", va='center', fontsize=8)
ax.set_yticks(range(len(top)), [label(r) for r in top])
ax.set_xlim(0, 395)
ax.set_xticks([0, 100, 200, 300])
ax.xaxis.grid(True, color=GRID)
ax.set_xlabel('Articles per five-year period', labelpad=8)
fig.text(.025, .035, 'Green: growth. Blue: decline. Open circle: earlier period; filled: later.', fontsize=8)
flags(ax, top)
save(fig, 'research-momentum-v5')

venues = nyu_journals()
selected = [next(r for r in venues if r['journal'] == j) for j in
    ['Philosophical Studies', 'Analysis', 'Philosophy and Phenomenological Research', 'The Philosophical Review']]
selected.append({'journal': 'All other journals', **{k: sum(r[k] for r in venues if r not in selected)
    for k in ['articles_2015_2019', 'articles_2020_2024', 'change']}})
fig, ax = canvas("NYU's decline is concentrated in Philosophical Studies", 'NYU-affiliated articles in the same 31-journal corpus', 5.3, .37)
for y, r in enumerate(selected[::-1]):
    ax.barh(y+.17, r['articles_2015_2019'], height=.30, color=BLUE, alpha=.35)
    ax.barh(y-.17, r['articles_2020_2024'], height=.30, color=BLUE)
    ax.text(max(r['articles_2015_2019'],r['articles_2020_2024'])+1, y,
        f"{r['articles_2015_2019']} → {r['articles_2020_2024']}", va='center', fontsize=9)
ax.set_yticks(range(len(selected)), [r['journal'] for r in selected[::-1]])
ax.set_xlim(0, max(r['articles_2015_2019'] for r in selected)+13)
ax.xaxis.grid(True, color=GRID)
ax.set_xlabel('Articles', labelpad=8)
fig.text(.025, .035, 'Light blue: 2015–2019. Blue: 2020–2024.', fontsize=8)
save(fig, 'nyu-journal-change')
print('Generated four revised figures in PNG and SVG')
