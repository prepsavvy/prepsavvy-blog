"""Shared PrepSavvy research chart typography, tokens and source footer."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[1]
STYLE = json.loads((ROOT/'assets/chart-style.json').read_text())
BLUE, GRID = STYLE['primary'], STYLE['grid']
GREEN = '#168342'
for font in (ROOT/'assets/fonts').glob('*.ttf'):
    font_manager.fontManager.addfont(str(font))
plt.rcParams.update({'font.family': STYLE['font'], 'font.size': 10,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.spines.left': False,
    'svg.hashsalt': 'prepsavvy-research', 'svg.fonttype': 'path'})


def canvas(title, subtitle, height=5.5, left=.24):
    fig, ax = plt.subplots(figsize=(10,height), facecolor='white')
    fig.text(.025,.975,title,fontsize=16,weight='bold',va='top')
    fig.text(.025,.914,subtitle,fontsize=9,va='top')
    fig.subplots_adjust(left=left,right=.96,bottom=.16,top=.81)
    ax.tick_params(length=0,pad=7)
    ax.set_axisbelow(True)
    ax.spines['bottom'].set_color('#BFBFBF')
    ax.xaxis.grid(True,color=GRID)
    return fig,ax


def save(fig, output, filename, source):
    fig.text(.025,.035,source,fontsize=8)
    logo=fig.add_axes([.81,.018,.16,.045])
    logo.imshow(plt.imread(ROOT/'assets/prepsavvy-logo.png'))
    logo.axis('off')
    output.mkdir(parents=True,exist_ok=True)
    fig.savefig(output/(filename+'.png'),dpi=180,metadata={'Software':'PrepSavvy'})
    fig.savefig(output/(filename+'.svg'),metadata={'Date':None})
    plt.close(fig)
