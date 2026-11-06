"""Build Figure 6 from saved cohort estimates and an explicit reporting policy."""
from pathlib import Path
import csv
import hashlib
import json
import argparse
from verify_sources import verify

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir',type=Path,default=ROOT/'outputs')
args=parser.parse_args()
verify()
OUT = args.output_dir.resolve()
OUT.mkdir(exist_ok=True,parents=True)
DATA = ROOT/'data/biology'
SOURCES = ['cohort_estimates.tsv','pooling_influence.tsv','pooled.tsv']

def read(name):
    with (DATA / name).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))

EST = read('cohort_estimates.tsv')
POOL = read('pooled.tsv')
INFLUENCE = read('pooling_influence.tsv')
COHORTS = ['GSE234933', 'GSE181919', 'GSE310797']
LABELS = ['Cohort A', 'Cohort B', 'Cohort C']
INK = '#172E3A'
BLUE = '#146873'
PURPLE = '#77558C'
GRAY = '#58636B'
PALE = '#F0F4F5'
RULE = '#CBD3D7'

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 8.4, 'axes.labelsize': 8.4,
    'xtick.labelsize': 8.0, 'ytick.labelsize': 8.2,
    'axes.titlesize': 9, 'axes.titleweight': 'normal',
    'axes.spines.right': False, 'axes.spines.top': False,
    'axes.linewidth': .6, 'axes.edgecolor': GRAY, 'text.color': INK,
    'axes.labelcolor': INK, 'xtick.color': INK, 'ytick.color': INK,
    'pdf.fonttype': 42, 'ps.fonttype': 42, 'svg.fonttype': 'none',
    'savefig.facecolor': 'white', 'figure.facecolor': 'white',
})
fig = plt.figure(figsize=(6.5, 7.6))

def title(y, letter, text):
    fig.text(.025, y, letter, fontsize=10, fontweight='bold', va='top')
    fig.text(.068, y-.001, text, fontsize=9.0, fontweight='bold', va='top')

def get(cohort, analysis='primary', method='equal_t'):
    rows = [r for r in EST if r['cohort']==cohort and r['analysis']==analysis and r['method']==method]
    assert len(rows)==1
    return rows[0]

def effect(ax, y, row, color=BLUE, marker='o', size=4.1):
    val, lo, hi = (float(row[k]) for k in ('estimate','low','high'))
    assert lo <= val <= hi
    ax.errorbar(val, y, xerr=[[val-lo], [hi-val]], fmt=marker,
                color=color, markerfacecolor=color, markersize=size,
                elinewidth=.95, capsize=2, capthick=.65, zorder=4)

def axis(ax, xlim, ticks):
    ax.set_xlim(*xlim)
    ax.set_xticks(ticks)
    ax.axvline(0, color=GRAY, lw=.65, ls=':', zorder=0)
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='y', length=0)
    ax.tick_params(axis='x', width=.6, length=3, pad=2)

# A. Cohort and meta-analytic intervals. Different means retain distinct labels.
title(.98, 'A', 'LILRB4–SPP1 macrophage-signature association')
ax = fig.add_axes([.28, .765, .68, .152])
axis(ax, (-.22, .23), [-.2,-.1,0,.1,.2])
ys = [3.35, 2.4, 1.45, .25]
row_labels=[]
for cohort,label,y in zip(COHORTS,LABELS,ys):
    r=get(cohort)
    row_labels.append(f"{label} ({int(r['eligible'])}/{int(r['attempted'])})\n{cohort}")
    effect(ax,y+.12,r)
    effect(ax,y-.12,get(cohort,method='reml_hksj'),PURPLE,'s')
for method,offset,color,mark in [('equal_t',.12,BLUE,'o'),('reml_hksj',-.12,PURPLE,'s')]:
    r=next(r for r in POOL if r['method']==method)
    y=ys[-1]+offset
    ax.plot([float(r['pi_low']),float(r['pi_high'])],[y,y],color=color,lw=.8,ls='--',zorder=1)
    effect(ax,y,r,color,mark,4.6)
ax.axhline(.88,color=RULE,lw=.65)
ax.set_yticks(ys, row_labels+['Across 3 cohorts'])
ax.set_ylim(-.3,3.95)
ax.set_xlabel('Association estimate (correlation scale)',labelpad=3)
handles=[Line2D([0],[0],color=BLUE,marker='o',lw=.8,ms=4,label='Equal mean / t'),
         Line2D([0],[0],color=PURPLE,marker='s',lw=.8,ms=4,label='Fisher REML / HKSJ'),
         Line2D([0],[0],color=GRAY,ls='--',lw=.8,label='Cohort prediction interval')]
fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.52,.95),ncol=3,
           frameon=False,fontsize=8.0,columnspacing=1.2,handlelength=2.0,
           borderaxespad=0,labelspacing=.4)

# B. Prespecified primary estimator across all common sensitivities.
title(.705, 'B', 'Sensitivity of the equal-patient mean')
b_labels=['Primary: depth','Detection gate','No adjustment','Depth + CD68']
analyses=['primary','detection_gate','unadjusted','depth_cd68']
lefts=[.275,.505,.735]
for c,(cohort,label,left) in enumerate(zip(COHORTS,LABELS,lefts)):
    bx=fig.add_axes([left,.525,.205,.128])
    axis(bx,(-.19,.285),[-.1,0,.1,.2])
    bx.axhspan(2.65,3.35,color=PALE,zorder=-1)
    for yy,analysis in zip([3,2,1,0],analyses):
        effect(bx,yy,get(cohort,analysis))
    bx.set_ylim(-.45,3.55)
    bx.set_yticks([3,2,1,0],b_labels if c==0 else [])
    bx.set_title(label,pad=5)
    if c==1:
        bx.text(.98,.735,'n = 18',ha='right',va='center',transform=bx.transAxes,fontsize=8.0)
fig.text(.6,.486,'Mean residual correlation (95% CI)',ha='center',va='top',fontsize=8.4)

# C. Original-data summaries, with their native targets retained.
title(.452, 'C', 'Association summaries in the original cohorts')
comparators=[('pooled_Pearson','Pooled cells'),('stacked_residual_Pearson','Stacked residuals'),
             ('equal_t','Equal-patient mean'),('reml_hksj','Fisher REML')]
for c,(cohort,label,left) in enumerate(zip(COHORTS,LABELS,lefts)):
    cx=fig.add_axes([left,.267,.205,.128])
    axis(cx,(-.01,.105),[0,.05,.1])
    original=next(r for r in INFLUENCE if r['cohort']==cohort and r['scenario']=='original')
    for yy,(method,_) in zip([3,2,1,0],comparators):
        color = BLUE if method=='equal_t' else PURPLE if method=='reml_hksj' else GRAY
        marker = 's' if method=='reml_hksj' else 'o'
        cx.scatter(float(original[method]),yy,s=23,marker=marker,facecolor=color,
                   edgecolor=color,linewidth=.8,zorder=4)
    cx.set_ylim(-.45,3.55)
    cx.set_yticks([3,2,1,0],[lab for _,lab in comparators] if c==0 else [])
    cx.set_title(label,pad=5,fontsize=8.4)
fig.text(.6,.228,'Association estimate (native target)',ha='center',va='top',fontsize=8.4)

# D. Implemented reporting flow; intentionally no validated scientific J/width cutoff.
title(.201, 'D', 'Reporting workflow with an explicit analysis policy')
dx=fig.add_axes([.025,.021,.95,.16]);dx.set_axis_off();dx.set_xlim(0,1);dx.set_ylim(0,1)
def box(x,y,w,h,lines,face=PALE):
    dx.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.005,rounding_size=0.015',
                              facecolor=face,edgecolor=RULE,lw=.7))
    dx.text(x+w/2,y+h/2,lines,ha='center',va='center',fontsize=8.2,linespacing=1.28)
def arrow(a,b,label=None,offset=(0,0)):
    dx.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='-|>',lw=.8,color=GRAY,
                                             mutation_scale=8,shrinkA=2,shrinkB=2))
    if label:dx.text((a[0]+b[0])/2+offset[0],(a[1]+b[1])/2+offset[1],label,
                     ha='center',va='center',fontsize=8.0)
box(.005,.55,.285,.4,'Define target and rules\nList patients and exclusions\nSet cell and patient minima')
box(.355,.55,.29,.4,'Method-specific availability\nJ ≥ 2; finite positive uncertainty\nDeclared count floor met?')
box(.715,.55,.28,.4,'Report estimate + 95% CI\nInterval width and sensitivity\nEligible / attempted patients')
arrow((.29,.75),(.355,.75))
arrow((.645,.75),(.715,.75),'Yes',(0,.12))
box(.275,.08,.39,.29,'If not met: patient effects and reasons\nNo group estimate, interval or P value','#FFFFFF')
arrow((.50,.55),(.47,.37),'No',(-.07,0))
box(.715,.08,.28,.29,'Optional planning MDE\nEqual mean + external SD only','#FFFFFF')
arrow((.855,.55),(.855,.37))
fig.text(.025,.006,'Patient-count and width thresholds are configurable; their scientific validity has not been established.',
         fontsize=8.0,va='bottom')

BASE='Figure_6_Biological_demonstration_and_reporting'
fig.savefig(OUT/(BASE+'.pdf'),dpi=600,metadata={'Title':'Biological demonstration and reporting workflow','Author':'Jinwei Tang; Yunfan Lin; Linrui Cai; Yali Wen; Guangyang Chen; Li Huang'})
fig.savefig(OUT/(BASE+'.svg'))
fig.savefig(OUT/(BASE+'.png'),dpi=300)
fig.savefig(OUT/(BASE+'.tiff'),dpi=600,pil_kwargs={'compression':'tiff_lzw'})

# Record actual text extents to identify clipping at the fixed physical size.
fig.canvas.draw();renderer=fig.canvas.get_renderer();canvas=fig.bbox
outside=[]
for obj in fig.findobj(matplotlib.text.Text):
    if not obj.get_visible() or not obj.get_text():continue
    bb=obj.get_window_extent(renderer)
    if bb.x0<canvas.x0-.5 or bb.x1>canvas.x1+.5 or bb.y0<canvas.y0-.5 or bb.y1>canvas.y1+.5:
        outside.append(obj.get_text())

caption=('Figure 6. Biological demonstration and reporting workflow. '
         '(A) Cohorts A–C include 48/51, 19/20 and 15/16 eligible/attempted patients; solid bars are 95% t/HKSJ confidence intervals (modified Hartung–Knapp for cross-cohort means), and dashed bars are prediction intervals. '
         '(B) Equal-mean sensitivities vary adjustment and detection gating (cohort B: 18 eligible). '
         '(C) Points compare original pooled-cell, stacked-residual, equal-patient and Fisher REML estimates. '
         '(D) The reporting workflow uses study-specific eligibility and precision settings and an externally specified variance for minimum detectable effect calculations.')
assert len(caption.split()) <= 110
(OUT/(BASE+'_caption.txt')).write_text(caption+'\n',encoding='utf-8')

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest={
    'figure_id':'Figure 6','backend':'Python / matplotlib','matplotlib':matplotlib.__version__,
    'size_inches':[6.5,7.6],'font':'DejaVu Sans','minimum_font_pt':8.0,'panel_title_pt':9.0,
    'claim':'The cohort associations are small and specification-sensitive; original pooled-cell and patient-level summaries differ, while transparent reporting distinguishes inferential targets and feasibility.',
    'evidence_boundary':'Retrospective biological demonstration, not causal or treatment evidence; no universal sample-size/precision guideline is validated.',
    'sources':[{'path':'data/biology/'+k,'sha256':digest(DATA/k)} for k in SOURCES],
    'script':{'path':Path(__file__).name,'sha256':digest(Path(__file__))},
    'outputs':[{'path':p.name,'sha256':digest(p)} for p in sorted(OUT.glob(BASE+'.*'))],
    'caption':{'path':BASE+'_caption.txt','sha256':digest(OUT/(BASE+'_caption.txt'))},
    'qa':{'outside_canvas_text':outside,'visual_inspection_required_after_changes':True,'uncertainty':'95% mean CIs in A/B; three-cohort PIs in A; native-target original point estimates in C'},
    'practice_policy':{'scientific_thresholds_validated':False,'minimum_two':'mathematical calculability only','mde':'external-SD equal-mean planning approximation only'},
}
(OUT/(BASE+'_manifest.json')).write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'outputs':[x['path'] for x in manifest['outputs']],'outside_canvas_text':outside},ensure_ascii=False))

if outside:
    raise RuntimeError('Text extends beyond Figure 6 canvas: '+repr(outside))
plt.close(fig)
