"""Draw Figures 1, 2 and 5 only from completed, recorded analyses.

The unified negative-binomial simulation is not a source of these figures.
Run with the repository requirements. No statistical fits occur here.
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

import os
import matplotlib
from verify_sources import verify

ROOT = Path(__file__).resolve().parents[1]
verify()
OUT = Path(os.environ.get('PASE_FIGURE_OUTPUT', ROOT / 'outputs'))
OUT.mkdir(exist_ok=True, parents=True)
DATA = ROOT / 'data'
FONT = Path(matplotlib.get_data_path()) / 'fonts' / 'ttf'
for name, fname in [('PASE Sans','DejaVuSans.ttf'), ('PASE Sans Bold','DejaVuSans-Bold.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONT/fname)))
W = 468.0  # custom author layout: 6.5 inches; not a claimed journal limit
INK = '#182C37'; MUTED = '#354D59'; TEAL = '#007F76'; BLUE = '#0072B2'
RULE = '#B7C5CB'; PALE = '#EDF4F5'; ORANGE = '#B46416'; WHITE = '#FFFFFF'
SOURCES = {}

def rows(rel):
    path = DATA / rel
    SOURCES[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t' if path.suffix=='.tsv' else ','))

sim = rows('gaussian/comparison.csv')
influence = rows('biology/pooling_influence.tsv')
ref = rows('controls/positive_reference_summary.tsv')
shuffle = rows('controls/shuffle_summary.tsv')
runtime = rows('resources/summary.tsv')
native = rows('count_pilot/summary.tsv')
sc_count = rows('count_pilot/sc_summary.tsv')
memento = rows('controls/memento_tests.tsv')
sc_ref = []
for path in sorted((DATA/'controls').glob('sc_*.csv')):
    rr = rows(path.relative_to(DATA))
    assert len(rr)==1
    sc_ref.extend(rr)
assert len(sc_ref)==4

METHODS = [
 ('Pooled Pearson','pooled_pearson','pooled_pearson'),
 ('Pooled Spearman','pooled_spearman','pooled_spearman'),
 ('Donor aggregate','patient_mean_pearson','pseudobulk'),
 ('Mundlak slope','mundlak_ml_wald','mundlak'),
 ('Equal-patient t','pase_equal_t','equal_r_t'),
 ('REML–HKSJ','pase_reml_hksj','reml_hksj'),
]
SCENARIOS = [('global_null','Null'),('fixed_positive','Fixed'),('heterogeneous_positive','Varying')]

class Drawing:
    def __init__(self, name, height):
        self.name=name; self.h=height; self.text_boxes=[]
        self.c=Canvas(str(OUT/(name+'.pdf')), pagesize=(W,height), invariant=1)
        self.c.setTitle(name.replace('_',' '))
        self.c.setAuthor('Jinwei Tang; Yunfan Lin; Linrui Cai; Yali Wen; Guangyang Chen; Li Huang')
        self.c.setSubject('PASE manuscript figure; data-bound vector artwork')
    def text(self,x,y,s,size=8.5,bold=False,col=INK,align='left'):
        s=str(s);font='PASE Sans Bold' if bold else 'PASE Sans'
        width=pdfmetrics.stringWidth(s,font,size)
        left=x if align=='left' else x-width/2 if align=='center' else x-width
        assert 0<=left and left+width<=W, (self.name,s,left,width)
        assert 0<y<=self.h, (self.name,s,y)
        self.c.setFont(font,size); self.c.setFillColor(HexColor(col))
        self.c.drawString(left,self.h-y,s)
        self.text_boxes.append({'text':s,'x':left,'y':y,'width':width,'size_pt':size})
    def line(self,x1,y1,x2,y2,col=RULE,lw=.6,dash=None):
        self.c.setStrokeColor(HexColor(col));self.c.setLineWidth(lw)
        self.c.setDash(dash or []);self.c.line(x1,self.h-y1,x2,self.h-y2);self.c.setDash([])
    def rect(self,x,y,w,h,fill=PALE,stroke=RULE,r=4):
        self.c.setFillColor(HexColor(fill));self.c.setStrokeColor(HexColor(stroke));self.c.setLineWidth(.65)
        self.c.roundRect(x,self.h-y-h,w,h,r,stroke=1,fill=1)
    def title(self,y,letter,label,x=6):
        self.text(x,y,letter,11,True,TEAL);self.text(x+17,y,label,9,True)
    def symbol(self,x,y,style=0,color=TEAL,size=2.6):
        self.c.setStrokeColor(HexColor(color));self.c.setLineWidth(.9)
        self.c.setFillColor(HexColor(WHITE if style==0 else color))
        if style==0:self.c.circle(x,self.h-y,size,stroke=1,fill=1)
        elif style==1:
            p=self.c.beginPath();p.moveTo(x,self.h-y+size);p.lineTo(x+size,self.h-y)
            p.lineTo(x,self.h-y-size);p.lineTo(x-size,self.h-y);p.close();self.c.drawPath(p,stroke=1,fill=1)
        else:self.c.rect(x-size,self.h-y-size,2*size,2*size,fill=1,stroke=1)
    def arrow(self,x1,y1,x2,y2,col=MUTED):
        self.line(x1,y1,x2,y2,col,.8)
        a=math.atan2(y2-y1,x2-x1)
        for da in (-.46,.46):self.line(x2,y2,x2-4*math.cos(a+da),y2-4*math.sin(a+da),col,.8)
    def box(self,x,y,w,h,title,body,fill=PALE):
        self.rect(x,y,w,h,fill)
        self.text(x+9,y+17,title,8.8,True)
        for i,line in enumerate(body):self.text(x+9,y+34+12*i,line)
    def save(self):
        self.c.showPage();self.c.save()
        return {'figure':self.name,'width_pt':W,'height_pt':self.h,'text_boxes':self.text_boxes}

def fig1():
    d=Drawing('Figure_1_Patient_anchored_framework',536)
    d.title(14,'A','Same data, different inferential units')
    d.box(6,28,456,43,'Same normalized scores and donor identities',[
        'Anchor, predefined outcome, covariates and eligibility'])
    d.arrow(116,71,116,88);d.arrow(351,71,351,88)
    d.rect(6,88,221,111,fill='#F1F4F6')
    d.rect(241,88,221,111)
    d.text(15,105,'Pooled-cell summary',8.8,True)
    d.text(250,105,'Patient-level summary',8.8,True)
    # Conceptual cells only: the same 9/4/2 illustrative cells enter both routes.
    # Colours + shapes identify donors. These are not measured cohort counts.
    for dx in (25,37,49):
        for yy in (120,132,144):d.symbol(dx,yy,0,BLUE,2.3)
    for dx in (62,74):
        for yy in (120,132):d.symbol(dx,yy,2,ORANGE,2.1)
    for dx in (62,74):d.symbol(dx,144,1,TEAL,2.5)
    d.arrow(90,132,130,132)
    d.text(141,135,'One estimate',8.5,True)
    d.text(15,174,'Contribution depends on cell yield')
    d.text(15,186,'Cell-weighted summary')
    for dx in (253,260,267):
        for yy in (118,123,128):d.symbol(dx,yy,0,BLUE,1.7)
    for dx in (253,260):
        for yy in (139,144):d.symbol(dx,yy,2,ORANGE,1.7)
    for dx in (253,260):d.symbol(dx,158,1,TEAL,2)
    for y,label in [(123,'Donor 1 association'),(141.5,'Donor 2 association'),(158,'Donor 3 association')]:
        d.arrow(280,y,314,y);d.text(324,y+2.5,label)
    d.text(250,174,'One association per donor')
    d.text(250,186,'Explicit aggregation target')
    # Only the patient route continues to patient-local residualization.
    d.arrow(351,199,351,219)
    d.box(6,219,456,48,'Within each donor',[
        'Residualize both scores; calculate correlation and information estimate'])
    d.arrow(234,267,234,279)
    d.title(292,'B','Choose the target before selecting a summary')
    d.box(6,305,145,94,'Equal-patient t',[
        'Population mean of', 'observed donor correlations', 'Equal donor contributions', 'Student t interval'])
    d.box(161,305,145,94,'Random effects',[
        'Population Fisher mean', 'REML variance estimate', 'HKSJ interval', 'Back-transform for display'])
    d.box(316,305,146,94,'Empirical Bayes',[
        'Individual donor effects', 'Shrink donor Fisher effects', 'Conditional on fitted', 'population parameters'],fill='#F7F1E8')
    for x in (79,234,389):d.arrow(x,399,x,416)
    d.box(6,416,456,45,'Report the target, uncertainty and analysis availability',[
        'Attempted and eligible donors; effect distribution; failure and influence diagnostics'])
    d.title(482,'C','Evaluate statistical performance and biological transportability')
    for x,title,body in [(6,'Simulation and method comparisons','Completed Gaussian and count controls'),
                         (241,'Three independent RNA cohorts','Fixed published SPP1 signature')]:
        d.rect(x,493,221,36);d.text(x+9,510,title,8.8,True);d.text(x+9,522,body)
    return d.save()

def fig2():
    d=Drawing('Figure_2_Donor_dependence_and_influence',468)
    d.title(14,'A','Gaussian evidence: false-positive risk with clustered cells')
    d.text(29,29,'8 donors; 2,000 datasets per allocation; 95% Wilson intervals',col=MUTED)
    for x,label,style,color in [(155,'80 cells per donor',0,BLUE),(299,'Unequal: 20–260 cells',1,ORANGE)]:
        d.symbol(x,44,style,color);d.text(x+7,47,label)
    x0=150;x1=454;sx=lambda v:x0+(x1-x0)*v/.6
    d.line(sx(.05),56,sx(.05),132,MUTED,.6,[2,2])
    for n,(label,key,_) in enumerate([METHODS[0],METHODS[1],METHODS[4]]):
        y=69+n*26;d.text(6,y+3,label)
        for off,allocation,style,color in [(-4,'equal80',0,BLUE),(4,'unequal',1,ORANGE)]:
            r=next(r for r in sim if r['allocation']==allocation and r['scenario']=='global_null' and r['method']==key)
            lo,hi,v=[float(r[k]) for k in ['wilson95_lo','wilson95_hi','rate_among_available']]
            d.line(sx(lo),y+off,sx(hi),y+off,color,1)
            d.line(sx(lo),y+off-2,sx(lo),y+off+2,color,.7)
            d.line(sx(hi),y+off-2,sx(hi),y+off+2,color,.7)
            d.symbol(sx(v),y+off,style,color)
    d.line(x0,143,x1,143,INK)
    for v in (0,.1,.2,.3,.4,.5,.6):
        xx=sx(v);d.line(xx,143,xx,147,INK);d.text(xx,158,f'{100*v:.0f}',align='center')
    d.text((x0+x1)/2,175,'Type-I error (%)  ·  dashed line: nominal 5%',align='center')
    d.title(201,'B','One donor repeated tenfold: sensitivity differs across cohorts')
    d.text(29,216,'LILRB4–SPP1 signature association; processed scores held fixed',col=MUTED)
    d.symbol(198,230,0,INK);d.text(205,233,'Original')
    d.symbol(293,230,1,TEAL);d.text(300,233,'Largest donor ×10')
    sx=lambda v:198+(v+.15)/.35*256
    display=[('Pooled cells','pooled_Pearson'),('Stacked residuals','stacked_residual_Pearson'),('Equal-patient mean','equal_t')]
    chosen=[]
    for i,cohort in enumerate(['GSE234933','GSE181919','GSE310797']):
        r0=next(r for r in influence if r['cohort']==cohort and r['scenario']=='original')
        r1=next(r for r in influence if r['cohort']==cohort and r['scenario']=='largest_tenfold')
        chosen.extend([r0,r1]);y=253+i*58
        d.text(6,y,f"{cohort}  ·  {r0['eligible']} eligible donors  ·  {r0['largest_donor']} share: {100*float(r0['largest_cell_share']):.1f}% → {100*float(r1['largest_cell_share']):.1f}%",8.5,True)
        d.line(sx(0),y+7,sx(0),y+46,RULE,.6,[2,2])
        for j,(label,key) in enumerate(display):
            yy=y+16+j*13;d.text(17,yy+2.5,label)
            a,b=float(r0[key]),float(r1[key]);d.line(sx(a),yy-1.5,sx(b),yy+1.5,MUTED,.8)
            d.symbol(sx(a),yy-1.5,0,INK,2.3);d.symbol(sx(b),yy+1.5,1,TEAL,2.3)
        assert float(r0['equal_t'])==float(r1['equal_t'])
    d.line(198,431,454,431,INK)
    for v in (-.15,-.1,0,.1,.2):
        xx=sx(v);d.line(xx,431,xx,435,INK);d.text(xx,446,f'{v:.2f}',align='center')
    d.text(326,462,'Association estimate (method-specific target)',align='center')
    return d.save(),chosen

def heat_color(p):
    # Sequential pale blue -> navy, with readable white labels only on dark cells.
    a=(241,246,248);b=(22,84,118)
    return '#'+''.join(f'{round(u+(v-u)*p):02x}' for u,v in zip(a,b))

def fig5():
    d=Drawing('Figure_5_Method_benchmarks',512)
    d.title(14,'A','Gaussian controls: rejection of zero across method-specific tests')
    d.text(29,29,'8 donors; n = 2,000 per scenario and allocation; numbers are percentages',col=MUTED)
    centers=[169,222,275,328,381,434]
    d.text(222,47,'80 cells per donor',8.5,True,align='center')
    d.text(381,47,'Unequal: 20–260 cells',8.5,True,align='center')
    for x,(_,label) in zip(centers,SCENARIOS*2):d.text(x,63,label,align='center')
    for i,(label,key,_) in enumerate(METHODS):
        y=77+i*17;d.text(6,y+11,label)
        for j,(allocation,scenario) in enumerate([(a,s) for a in ('equal80','unequal') for s,_ in SCENARIOS]):
            r=next(r for r in sim if r['method']==key and r['scenario']==scenario and r['allocation']==allocation)
            v=float(r['rate_among_available']);d.rect(centers[j]-25,y,50,15,heat_color(v),WHITE,r=0)
            d.text(centers[j],y+10.7,str((Decimal(str(v))*Decimal(100)).quantize(Decimal('0.1'),rounding=ROUND_HALF_UP)),col=WHITE if v>=.65 else INK,align='center')
    d.text(6,194,'Null: type-I error. Fixed / varying: native rejection rates, not a common-target ranking.',8.5,col=MUTED)
    d.title(218,'B','Real-data checks')
    d.title(218,'C','Single-pair resources',x=242)
    d.text(6,233,'19 donors; 4 selected reference pairs',col=MUTED)
    d.text(242,233,'20 donors; 32 genes; 3 successful runs',col=MUTED)
    d.text(6,248,'Method',8.5,True)
    d.text(135,248,'Calls / valid',8.5,True,align='center')
    d.text(207,248,'Shuffle',8.5,True,align='center')
    d.text(135,259,'of 4 pairs',align='center');d.text(207,259,'of 999',align='center')
    d.line(6,264,233,264,MUTED)
    pmap={r['method']:r for r in ref}
    smap={r['method']:r for r in shuffle if r['pair']=='LILRB4--MMP14'}
    mrefs=[r for r in memento if r['mode']=='donor_mean_original' and r['pair']!='LILRB4--MMP14' and r['status']=='native_finite']
    scvalid=[r for r in sc_ref if r['status']=='ok']
    refrows=[]
    for i,(label,_,rid) in enumerate(METHODS+[('memento','memento','memento'),('scCOSMiX','scCOSMiX','scCOSMiX')]):
        if rid=='memento':
            valid=len(mrefs);calls=sum(float(r['native_coefficient'])>0 and float(r['native_two_sided_p'])<.05 for r in mrefs)
        elif rid=='scCOSMiX':
            valid=len(scvalid);calls=sum(float(r['fixed_rho'])>0 and float(r['fixed_z_wald_p'])<.05 for r in scvalid)
        else:valid=int(pmap[rid]['evaluable_pairs']);calls=int(pmap[rid]['nominal_positive'])
        y=278+i*14;d.text(6,y,label);d.text(135,y,f'{calls} / {valid}',align='center')
        s=smap.get(rid); sh=f"{s['rejections']}" if s else '—'
        if rid=='pseudobulk':sh+='*'
        d.text(207,y,sh,align='center');d.line(6,y+4,233,y+4,'#E6EDEF',.5)
        refrows.append({'method':rid,'attempted_pairs':4,'valid':valid,'nominal_positive':calls,'shuffle_rejected':s['rejections'] if s else None,'shuffle_attempted':999 if s else None})
    d.text(6,402,'Shuffle: LILRB4–MMP14 within donors.',8.5,col=MUTED)
    d.text(6,414,'* Donor aggregate unchanged by shuffling.',8.5,col=MUTED)
    rmap={(r['method'],int(r['cells'])):r for r in runtime}
    for x,label in [(336,'10k'),(369,'100k'),(402,'1M'),(445,'MiB')]:d.text(x,248,label,8.5,True,align='center')
    d.text(242,259,'Time (s); memory at 1M cells',col=MUTED);d.line(242,264,462,264,MUTED)
    for i,(label,key) in enumerate([('Pearson','pooled_pearson'),('Spearman','pooled_spearman'),('Donor aggregate','pseudobulk'),('Mundlak','mundlak'),('PASE summaries','pase_all'),('memento','memento'),('scCOSMiX','scCOSMiX')]):
        yy=278+i*14;d.text(242,yy,label)
        for x,n in zip((336,369,402),(10000,100000,1000000)):
            r=rmap[key,n];v=f"{float(r['successful_median_wall_s']):.2f}" if r['successful_median_wall_s'] else '>120'
            d.text(x,yy,v,align='center')
        mr=rmap[key,1000000]
        mv=f"{float(mr['successful_median_peak_MiB']):.0f}" if mr['successful_median_peak_MiB'] else f"{float(mr['last_attempt_peak_MiB']):.0f}*"
        d.text(445,yy,mv,align='center')
        d.line(242,yy+4,462,yy+4,'#E6EDEF',.5)
    d.text(242,388,'scCOSMiX: 1 attempt; * memory at timeout.',8.5,col=MUTED)
    d.text(242,402,'PASE: 3 summaries; memento: donor',8.5,col=MUTED)
    d.text(242,414,'moments, without bootstrap tests.',8.5,col=MUTED)
    d.title(439,'D','Count-input pilot: rejected / usable fits (8 donors)')
    cols=[(159,'Equal t (n=100)'),(256,'REML–HKSJ (100)'),(351,'memento (100)'),(430,'scCOSMiX (12)')]
    for x,label in cols:d.text(x,456,label,8.0,True,align='center')
    d.line(6,462,462,462,MUTED)
    nmap={(r['scenario'],r['method']):r for r in native}
    scmap={r['setting']:r for r in sc_count}
    for i,(scenario,label) in enumerate(SCENARIOS):
        yy=476+i*14;d.text(6,yy,label)
        for (x,_),key in zip(cols[:3],['pase_equal_t','pase_reml_hksj','memento_conditional_mean']):
            r=nmap[scenario,key];d.text(x,yy,f"{r['reject']} / {r['valid']}",align='center')
        r=scmap[scenario];d.text(430,yy,f"{r['nominal_calls']} / {r['reported']}",align='center')
    return d.save(),refrows

def render(name, height):
    import pypdfium2 as pdfium
    from PIL import Image
    with pdfium.PdfDocument(OUT/(name+'.pdf')) as pdf:
        page = pdf[0]
        for dpi, ext in [(300,'png'), (600,'tiff')]:
            bitmap = page.render(scale=dpi/72 - 1e-12)
            im = bitmap.to_pil()
            kwargs = {'dpi':(dpi,dpi)}
            if ext=='tiff': kwargs['compression']='tiff_lzw'
            im.save(OUT/(name+'.'+ext), **kwargs)
            im.close()
            bitmap.close()
        page.close()
    with Image.open(OUT/(name+'.png')) as im: pngsize=list(im.size)
    with Image.open(OUT/(name+'.tiff')) as im: tifsize=list(im.size)
    return {'pdf_points':[0,0,W,height], 'png_pixels':pngsize, 'tiff_pixels':tifsize,
            'png_dpi':300, 'tiff_dpi':600}


def build(number):
    result = {1:fig1, 2:fig2, 5:fig5}[number]()
    meta = result[0] if isinstance(result,tuple) else result
    meta['export'] = render(meta['figure'], meta['height_pt'])
    meta['font'] = 'DejaVu Sans'
    meta['source_manifest_sha256'] = hashlib.sha256((ROOT/'source_manifest.json').read_bytes()).hexdigest()
    meta['scope'] = 'Reconstruction from archived aggregate outputs; no raw-data refits are performed.'
    meta['outputs'] = [{'path':meta['figure']+'.'+ext, 'sha256':hashlib.sha256((OUT/(meta['figure']+'.'+ext)).read_bytes()).hexdigest()} for ext in ['pdf','png','tiff']]
    caption = ROOT/'captions'/(meta['figure']+'.txt')
    (OUT/(meta['figure']+'_caption.txt')).write_bytes(caption.read_bytes())
    (OUT/(meta['figure']+'_manifest.json')).write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'figure':number,'output_dir':str(OUT),'files':[x['path'] for x in meta['outputs']]}))
