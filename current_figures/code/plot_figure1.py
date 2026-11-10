"""Compact, editable Figure 1 schematic. No empirical analysis is performed.

All geometry is illustrative. Existing schematic cell coordinates and patient
effect positions are retained; explanatory prose is carried by the caption.
"""
from pathlib import Path
from datetime import datetime,timezone
import csv,json,hashlib,itertools,os
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Polygon,Rectangle,FancyArrowPatch
from matplotlib.text import Text
import fitz
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ['PASE_FIGURE_OUTPUT_DIR']).resolve()
OLD=ROOT/'schematic'  # Frozen illustrative coordinates, not empirical observations.
from font_policy import resolve_fonts
FONT_INFO=resolve_fonts()
W,H=180,133
BLUE='#0072B2'; VERM='#D55E00'; INK='#151515'; GRAY='#737373'; RULE='#C5C5C5'
PC=['#009E73','#686868','#CC79A7']; PM=['o','^','D']
mpl.rcParams.update({'font.family':FONT_INFO['family'],'font.size':7.5,'pdf.fonttype':42,'ps.fonttype':42,
                    'svg.fonttype':'none','axes.linewidth':.5,'axes.labelcolor':INK,
                    'text.color':INK,'figure.facecolor':'white','savefig.facecolor':'white'})
fig=plt.figure(figsize=(W/25.4,H/25.4))
canvas=fig.add_axes([0,0,1,1]);canvas.set_xlim(0,W);canvas.set_ylim(0,H);canvas.axis('off')
def txt(x,y,s,size=7.5,bold=False,ha='left',color=INK,**kw):
    return canvas.text(x,y,s,fontsize=size,fontweight='bold' if bold else 'normal',ha=ha,va='center',color=color,**kw)
def arrow(a,b,color=GRAY,width=.8):
    canvas.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=8,lw=width,color=color))
def axes(x,y,w,h,xlim=None,ylim=None):
    a=fig.add_axes([x/W,y/H,w/W,h/H]);a.set_xticks([]);a.set_yticks([])
    a.spines[['right','top']].set_visible(False)
    a.spines[['left','bottom']].set_color(GRAY);a.spines[['left','bottom']].set_linewidth(.5)
    if xlim:a.set_xlim(*xlim)
    if ylim:a.set_ylim(*ylim)
    return a
def person(x,y,color=GRAY,scale=1):
    canvas.add_patch(Circle((x,y+2.6*scale),1.1*scale,facecolor=color,edgecolor='none'))
    canvas.add_patch(Polygon([(x-1.6*scale,y+.9*scale),(x+1.6*scale,y+.9*scale),(x+2*scale,y-2*scale),(x-2*scale,y-2*scale)],closed=True,facecolor=color,edgecolor='none'))

cells=list(csv.DictReader((OLD/'schematic_cell_geometry.csv').open(encoding='utf-8')))
summary=list(csv.DictReader((OLD/'schematic_summary_geometry.csv').open(encoding='utf-8')))
r=np.array([float(x['r_position']) for x in summary]);z=np.array([float(x['z_position']) for x in summary])
se=np.array([float(x['illustrative_se']) for x in summary]);weights=np.array([float(x['weight']) for x in summary])
shrunk=np.array([float(x['shrunk_z_position']) for x in summary]);mu=float(np.sum(weights*z)/weights.sum())

# A: identical illustrative cells in the pooled and patient-specific views.
txt(2,129,'A',10,True,color='#000000');txt(8,129,'Association',8.3,True)
txt(29,122.5,'Pooled cells',8,True,ha='center')
txt(123,122.5,'Within patients',8,True,ha='center')
ap=axes(12,101,34,17,(-1.28,1.24),(-.84,.91))
offsets=[(-.70,.45),(0,0),(.72,-.42)]
patient_axes=[]
for i,((dx,dy),color,marker) in enumerate(zip(offsets,PC,PM),1):
    cc=[c for c in cells if int(c['schematic_patient'])==i]
    xp=np.array([float(c['x']) for c in cc]);yp=np.array([float(c['y']) for c in cc])
    ap.scatter(xp,yp,s=13,c=color,marker=marker,edgecolors=INK,linewidths=.25,zorder=3)
    xx=82+(i-1)*30
    ai=axes(xx,101,23,17,(dx-.56,dx+.56),(dy-.42,dy+.42))
    ai.scatter(xp,yp,s=13,c=color,marker=marker,edgecolors=INK,linewidths=.25,zorder=3)
    ai.plot([dx-.5,dx+.5],[dy-.325,dy+.325],color=GRAY,lw=.6,ls='--',zorder=1)
    txt(xx+11.5,119.5,f'P{i}',7.2,ha='center',color=color)
    txt(xx+11.5,97.8,f'r{i}',7.5,ha='center')
    patient_axes.append(ai)
ap.plot([-1.15,1.12],[.44,-.43],color=GRAY,lw=.6,ls='--',zorder=1)
txt(29,97.8,'Anchor',7.2,ha='center');txt(8.4,109.5,'Score',7.2,ha='center',rotation=90)
arrow((54,109.5),(73,109.5))
arrow((123,94.6),(123,90.8));canvas.plot([90,123],[90.8,90.8],color=GRAY,lw=.7);arrow((90,90.8),(90,87.7))

# B: short target labels accompany the three distinct geometric summaries.
txt(2,86,'B',10,True,color='#000000');txt(8,86,'Summaries',8.3,True)
centers=[31,90,149]
for cx,title,col in zip(centers,['Equal-patient t','REML–HKSJ','Empirical Bayes'],[BLUE,VERM,INK]):
    txt(cx,79.9,title,8,True,ha='center')
    canvas.plot([cx-23,cx+23],[77.2,77.2],color=col,lw=1.0)
ys=np.array([.73,.49,.25])
a=fig.add_axes([13/W,57/H,39/W,18/H]);a.set_xlim(-.10,1);a.set_ylim(.02,.93);a.axis('off')
a.axvline(float(np.mean(r)),color=GRAY,lw=.65,ls='--')
a.text(float(np.mean(r)),.9,'mean r',ha='center',fontsize=7,color=GRAY)
for i,(p,y) in enumerate(zip(r,ys),1):
    a.scatter(p,y,s=24,color=BLUE,marker='o',zorder=3)
    a.text(-.12,y,f'P{i}',fontsize=7.2,ha='right',va='center')
a.plot([0,.96],[.10,.10],color=GRAY,lw=.5);a.plot([0,0],[.08,.12],color=INK,lw=.5)
a.text(0,.06,'0',ha='center',va='top',fontsize=7.2)

for base,eb in [(72,False),(131,True)]:
    a=fig.add_axes([base/W,57/H,39/W,18/H]);a.set_xlim(-.15,1.4);a.set_ylim(.02,.93);a.axis('off')
    a.axvline(mu,color=GRAY,lw=.65,ls='--');a.text(mu,.9,'mean z',ha='center',fontsize=7,color=GRAY)
    for i,(p,q,y,s,w) in enumerate(zip(z,shrunk,ys,se,weights),1):
        if eb:
            a.scatter(p,y,s=21,facecolors='white',edgecolors=GRAY,marker='o',lw=.7,zorder=3)
            a.annotate('',xy=(q,y),xytext=(p,y),arrowprops={'arrowstyle':'-|>','color':GRAY,'lw':.85,'mutation_scale':7,'shrinkA':3,'shrinkB':3},zorder=2)
            a.scatter(q,y,s=17,color=INK,marker='o',zorder=4)
        else:
            a.plot([p-1.3*s,p+1.3*s],[y,y],color=VERM,lw=.75)
            a.scatter(p,y,s=50*w/weights.max(),color=VERM,marker='s',zorder=3)
        a.text(-.19,y,f'P{i}',fontsize=7.2,ha='right',va='center')
    a.plot([-.10,1.34],[.10,.10],color=GRAY,lw=.5);a.plot([0,0],[.08,.12],color=INK,lw=.5)
    a.text(0,.06,'0',ha='center',va='top',fontsize=7.2)
for cx,lab in zip(centers,['Correlation r','Fisher z','Patient z']):txt(cx,52.8,lab,7.2,ha='center')

# A compact report strip uses icons and labels; detailed defaults are in caption.
canvas.plot([8,172],[49.5,49.5],color=RULE,lw=.6)
person(47,44,INK,.75);txt(51,44,'Included',7.2)
person(80,44,'#B0B0B0',.75);canvas.plot([78.6,81.4],[42.2,45.5],color=GRAY,lw=.75);txt(84,44,'Excluded',7.2)
canvas.add_patch(Polygon([(119.3,42),(122,46.5),(124.7,42)],closed=True,facecolor='white',edgecolor=INK,lw=.7))
txt(122,43.5,'!',7,True,ha='center');txt(127,44,'Warnings',7.2)
arrow((90,39.7),(90,36.8))

# C: illustrative evidence icons, rather than prose boxes or data-like claims.
txt(2,34.8,'C',10,True,color='#000000');txt(8,34.8,'Evaluation',8.3,True)
txt(46,29,'Benchmarks',8,True,ha='center');txt(135,29,'HNSCC',8,True,ha='center')
# Monochrome miniature matrix: arbitrary illustrative cells, no numeric values.
mini=np.array([[.1,.2,.6,.3,.2],[.5,.3,.2,.6,.1],[.2,.8,.3,.4,.6],[.6,.5,.2,.2,.3]])
for iy,row in enumerate(mini):
    for ix,v in enumerate(row):
        col=tuple(1-v*.62 for _ in range(3))
        canvas.add_patch(Rectangle((16+ix*2.8,12+iy*2.8),2.6,2.6,facecolor=col,edgecolor='none'))
# A tiny reference comparison chart, labelled only by its figure destination.
canvas.plot([39,72],[12,12],color=GRAY,lw=.55);canvas.plot([39,39],[12,24],color=GRAY,lw=.55)
canvas.plot([42,52,62,70],[15,17,19,22],color=BLUE,lw=.9,marker='o',ms=2.4)
canvas.plot([42,52,62,70],[14,18,17,20],color=VERM,lw=.9,marker='s',ms=2.2)
txt(46,7.5,'Figs. 2–5',7.5,ha='center')
# Three schematic cohort clusters. Different point sizes suggest unequal yields.
for ci,cx in enumerate([116,135,154]):
    for j,dx in enumerate([-4,0,4]):person(cx+dx,21,PC[j],.55)
    for dx,dy,s,c in [(-4,14,3.3,PC[0]),(0,16,2.1,PC[1]),(4,12.8,1.35,PC[2])]:
        canvas.plot(cx+dx,dy,'o',color=c,ms=s,mec=INK,mew=.2)
txt(135,7.5,'Fig. 6',7.5,ha='center')
canvas.plot([90,90],[35.8,31.6],color=GRAY,lw=.7);canvas.plot([46,135],[31.6,31.6],color=GRAY,lw=.7)
arrow((46,31.6),(46,30.5));arrow((135,31.6),(135,30.5))

fig.canvas.draw();renderer=fig.canvas.get_renderer();texts=[]
for t in fig.findobj(Text):
    if not t.get_visible() or not t.get_text().strip():continue
    b=t.get_window_extent(renderer)
    texts.append({'text':t.get_text(),'size_pt':t.get_fontsize(),'bbox':[b.x0,b.y0,b.x1,b.y1]})
outside=[t for t in texts if t['bbox'][0]<-.5 or t['bbox'][1]<-.5 or t['bbox'][2]>fig.bbox.width+.5 or t['bbox'][3]>fig.bbox.height+.5]
overlap=[]
for a,b in itertools.combinations(texts,2):
    x,y=a['bbox'],b['bbox']
    if min(x[2],y[2])-max(x[0],y[0])>1 and min(x[3],y[3])-max(x[1],y[1])>1:overlap.append([a['text'],b['text']])
assert not outside,outside
meta={'Title':'Patient-level association workflow','Author':'Jinwei Tang; Yunfan Lin; Linrui Cai; Yali Wen; Guangyang Chen; Li Huang','Creator':'PASE authors'}
for ext,kw in [('svg',{}),('pdf',{'metadata':meta}),('png',{'dpi':300}),('tiff',{'dpi':600,'pil_kwargs':{'compression':'tiff_lzw'}})]:fig.savefig(OUT/f'Figure_1.{ext}',**kw)
plt.close(fig)
d=fitz.open(OUT/'Figure_1.pdf');d[0].get_pixmap(dpi=160,alpha=False).save(OUT/'Figure_1_PDF_preview.png')
ti=Image.open(OUT/'Figure_1.tiff')
caption=('Figure 1. Patient-level association workflow. '
'(A) Identical schematic cells are pooled or analysed within patients after depth adjustment; colours and shapes identify patients. '
'(B) Equal-patient t, REML–HKSJ and empirical Bayes target the mean patient correlation, a population Fisher-scale mean and individual patient effects, respectively; equal point areas, weight-proportional square areas and shrinkage arrows illustrate the summaries, while dashed lines mark the labelled means and separate ticks mark zero. '
'The report icons denote method-eligible patients, excluded patients and warnings; PASE 1.1.0 defaults to descriptive output below 6 eligible patients and warns below 20 or when the full interval width exceeds 0.2, with these configurable defaults remaining reporting choices rather than validated adequacy thresholds. '
'(C) Benchmarks (Figures 2–5) and the three-cohort HNSCC application (Figure 6) evaluate and illustrate the workflow; all geometry is schematic, and the summary positions in B are not calculated from the cells in A.')
(OUT/'Figure_1_caption.txt').write_text(caption+'\n',encoding='utf-8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['schematic_cell_geometry.csv','schematic_summary_geometry.csv']:(OUT/name).write_bytes((OLD/name).read_bytes())
qa={'width_mm':W,'height_mm':H,'minimum_text_pt':min(t['size_pt'] for t in texts),'text_items':len(texts),
    'outside_text':outside,'overlapping_text':overlap,'visible_words':len(' '.join(t['text'] for t in texts).split()),
    'pdf_raster_count':len(d[0].get_images()),'pdf_fonts':[f[3] for f in d[0].get_fonts(full=True)],
    'tiff_dpi':[float(x) for x in ti.info.get('dpi',[])],'tiff_pixels':list(ti.size),'svg_text_count':(OUT/'Figure_1.svg').read_text(encoding='utf-8').count('<text'),
    'original_geometry_preserved':all(sha(OUT/n)==sha(OLD/n) for n in ['schematic_cell_geometry.csv','schematic_summary_geometry.csv']),
    'short_labels_only':True,'prose_boxes_removed':True,'no_gray_subtitles_or_footnotes':True,'simulation_icon_is_schematic':True,
    'A_positive_within_patient_signs':True,'B_positive_patient_effects':r.tolist(),'patient_colours':PC,
    'method_colours':{'equal_patient':BLUE,'random_effects':VERM},'Origin_used':False,'AI_imagegen_used':False,
    'scientific_analysis_performed':False,'font_policy':FONT_INFO,'visual_QA':'not performed by this command','artifacts':{ext:sha(OUT/f'Figure_1.{ext}') for ext in ['pdf','svg','png','tiff']}}
(OUT/'Figure_1_composition.json').write_text(json.dumps(qa,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'outside':outside,'overlaps':overlap,'words':qa['visible_words'],'rasters':qa['pdf_raster_count']}))
