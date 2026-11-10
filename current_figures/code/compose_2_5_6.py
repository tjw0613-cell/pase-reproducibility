"""Compose Figures 2, 5 and 6 from this revision's native Origin PDFs.

No data mark, interval, curve, count or statistical result is drawn here.
Only native-size panel placement, short labels and legend keys are added.
Run after panel verification: python compose_2_5_6.py --figures 2 5 6
"""
from pathlib import Path
import argparse
import math
import fitz
from compose_5_6 import (
    Composer, ROOT, OUT, PANELS, PLANS, spec, load_csv, MM, rgb,
    BLACK, BLUE, VERM, SCENARIOS, SCENARIO_LABELS, COHORTS, draw_q,
)

DARK = '#333333'
LIGHT = '#ACACAC'
METHODS = {
    'pooled_pearson': 'Pooled Pearson',
    'pooled_spearman': 'Pooled Spearman',
    'pseudobulk': 'Pseudobulk Pearson',
    'mundlak': 'Mundlak slope',
    'equal_r_t': 'Equal-patient t',
    'reml_hksj': 'REML–HKSJ',
}
REQUIRED = {
    '2': ['F2A', 'F2C'] + ['F2B_' + x for x in COHORTS],
    '5': ['F5B', 'F5C'] + ['F5A_' + x for x in SCENARIOS] + ['F5D_' + x for x in SCENARIOS],
    '6': ['F6A', 'F6C'] + ['F6B_' + x for x in COHORTS],
}


def legend_symbol(c, x, y, color, symbol=2, diameter_pt=3.5):
    """Legend key only; Origin symbol IDs 1/2/3/5 = square/circle/triangle/diamond."""
    r = diameter_pt / 2 / MM
    rect = fitz.Rect((x-r)*MM, (y-r)*MM, (x+r)*MM, (y+r)*MM)
    if symbol == 2:
        c.page.draw_oval(rect, color=rgb(color), fill=rgb(color), width=.4)
    elif symbol == 1:
        c.page.draw_rect(rect, color=rgb(color), fill=rgb(color), width=.4)
    else:
        points = ([(x,y-r),(x+r,y+r),(x-r,y+r)] if symbol == 3
                  else [(x,y-r),(x+r,y),(x,y+r),(x-r,y)])
        c.page.draw_polyline([(a*MM,b*MM) for a,b in points],
                             color=rgb(color), fill=rgb(color), closePath=True, width=.4)


def legend(c, x, y, label, color, symbol=2, connected=False, dashed=False, size=7.2):
    """Keys distinguish symbols and line types without altering any data panel."""
    if connected:
        c.page.draw_line((x*MM,(y-.8)*MM),((x+4)*MM,(y-.8)*MM),
                         color=rgb(color), width=.8, dashes='[2 2]' if dashed else None)
    legend_symbol(c, x+2, y-.8, color, symbol)
    c.text(x+6,y,label,size)


def x_position(s, value, left):
    lo,hi=s['xlim'][:2]
    fraction = ((math.log10(value)-math.log10(lo))/(math.log10(hi)-math.log10(lo))
                if s.get('x_scale') == 'log10' else (value-lo)/(hi-lo))
    return left + s['width_mm']*(s['layer_box'][0] + s['layer_box'][2]*fraction)/100


def bottom_axis(s, top):
    return top+s['height_mm']*(s['layer_box'][1]+s['layer_box'][3])/100


def figure2():
    c=Composer('Figure_2',208)
    c.panel_title('A','Null rejection',1,5)
    legend(c,44,11,'Equal allocation',DARK,2)
    legend(c,107,11,'Unequal allocation',LIGHT,1)
    top=14; s=c.place('F2A',35,top)
    for y,label in zip([3,2,1],s['row_labels']):
        c.text(33,c.y_data(s,y,top)+.9,label,7.5,align='right')
    c.text(107,60,'Type I error (%)',align='center')

    c.panel_title('B','Donor duplication',1,69)
    legend(c,44,75,'Original',DARK,2)
    legend(c,107,75,'Largest donor ×10',LIGHT,5)
    for i,cohort in enumerate(COHORTS):
        left=35+i*48; top=85
        c.text(left+24,82,cohort,7.5,True,align='center')
        s=c.place('F2B_'+cohort,left,top)
        if i==0:
            for y,label in zip([3,2,1],s['row_labels']):
                c.text(33,c.y_data(s,y,top)+.9,label,7.5,align='right')
    c.text(107,132,'Correlation',align='center')

    c.panel_title('C','Cells per patient',1,141)
    left=28;top=144;s=c.place('F2C',left,top)
    for category,cohort in enumerate(COHORTS,1):
        c.text(x_position(s,category,left),200,cohort,7.5,align='center')
    c.text(31,186,'Myeloid cells',7.5,rotate=90)
    c.save()


def figure5():
    c=Composer('Figure_5',233)
    c.panel_title('A','Gaussian benchmark',1,5)
    legend(c,44,12,'Equal allocation',DARK,2)
    legend(c,107,12,'Unequal allocation',LIGHT,1)
    for j,(scenario,label) in enumerate(zip(SCENARIOS,SCENARIO_LABELS)):
        left=36+j*47;top=22
        c.text(left+23.5,19,label,7.6,True,align='center')
        s=c.place('F5A_'+scenario,left,top)
        if j==0:
            for y,name in zip(range(6,0,-1),s['row_labels']):
                c.text(35,c.y_data(s,y,top)+.9,name,7.2,align='right')
    c.text(106.5,76,'Rejection (%)',align='center')

    c.panel_title('B','Shuffle rejections',1,86)
    c.panel_title('C','Runtime',96,86)
    left=35;top=89;s=c.place('F5B',left,top)
    # Origin's transposed category axis is top-to-bottom categories 1..6.
    for row,key in enumerate(s['method_order'],1):
        yy=top+s['height_mm']*(s['layer_box'][1]+s['layer_box'][3]*(row-.5)/6)/100
        c.text(34,yy+.9,METHODS[key],7.2,align='right')
        count=s['series'][0]['y'][row-1]
        xx=left+s['width_mm']*(s['layer_box'][0]+s['layer_box'][2]*count/s['ylim'][1])/100
        c.text(xx+1.3,yy+.9,str(count),7)
    c.text(63,150,'Rejections / 999 shuffles',7.2,align='center')
    left=95;top=89;s=c.place('F5C',left,top)
    for n,label in [(10000,'10k'),(100000,'100k'),(1000000,'1M')]:
        c.text(x_position(s,n,left),bottom_axis(s,top)+4,label,7.2,align='center')
    c.text(101,127,'Time (s)',7.2,rotate=90)
    c.text(140,150,'Cells',7.2,align='center')
    short={'pooled_pearson':'Pearson','pooled_spearman':'Spearman','pseudobulk':'Pseudobulk',
           'mundlak':'Mundlak','pase_all':'PASE','memento':'memento'}
    for i,row in enumerate(s['series']):
        # A 2-column × 3-row legend belongs directly below the runtime graph.
        x=102+(i%2)*38;y=158+(i//2)*6
        legend(c,x,y,short[row['label']],row['color'],row['symbol'],True,row.get('dash',False),7)

    c.panel_title('D','Native count benchmark',1,181)
    for j,(scenario,label) in enumerate(zip(SCENARIOS,SCENARIO_LABELS)):
        left=36+j*47;top=190
        c.text(left+23.5,188,label,7.6,True,align='center')
        s=c.place('F5D_'+scenario,left,top)
        if j==0:
            for y,name in zip([3,2,1],s['row_labels']):
                c.text(35,c.y_data(s,y,top)+.9,name,7.2,align='right')
    c.text(106.5,229,'Rejection (%)',align='center')
    c.save()


def figure6():
    c=Composer('Figure_6',234)
    c.panel_title('A','Patient associations',1,5)
    legend(c,39,11,'Equal-patient t',BLUE,2,True)
    legend(c,101,11,'REML–HKSJ',VERM,1,True)
    c.text(98,18,'Cells',7)
    for x,n in [(114,100),(134,500),(156,2500)]:
        legend_symbol(c,x,17.2,'#B0B0B0',2,10*math.sqrt(n/2602))
        c.text(x+3.2,18,str(n),7)
    left=38;top=21;s=c.place('F6A',left,top)
    for y,cohort in zip([3,2,1],COHORTS):
        c.text(37,c.y_data(s,y,top)+.9,cohort,7.5,align='right')
    c.text(107,100,'Correlation',align='center')

    c.panel_title('B','Cell thresholds',1,108)
    for i,cohort in enumerate(COHORTS):
        left=5+i*58;top=118
        c.text(left+29,115,cohort,7.5,True,align='center')
        s=c.place('F6B_'+cohort,left,top)
        for category,cutoff in enumerate([10,30,50],1):
            c.text(x_position(s,category,left),bottom_axis(s,top)+4,str(cutoff),7.2,align='center')
    c.text(2.7,153,'Correlation',7.5,rotate=90)
    c.text(93,169,'Minimum cells per patient',align='center')

    c.panel_title('C','Gating change',1,177)
    left=35;top=181;s=c.place('F6C',left,top)
    rows=load_csv(ROOT/'inputs/Figure6_C.csv')
    for y,cohort in zip([3,2,1],COHORTS):
        yy=c.y_data(s,y,top)
        c.text(34,yy+.9,cohort,7.5,align='right')
        row=next(r for r in rows if r['cohort']==cohort)
        draw_q(c,156,yy+.9,float(row['paired_t_q_BH_3_cohorts']))
    c.text(96,231,'Mean change in r',align='center')
    c.save()


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--figures',nargs='+',choices=['2','5','6'],default=['2','5','6'])
    args=ap.parse_args()
    missing=[x for f in args.figures for x in REQUIRED[f] if not (PANELS/x/'result.pdf').is_file()]
    if missing:raise SystemExit('Pending native Origin panels: '+', '.join(missing))
    for f in args.figures:globals()['figure'+f]()
    print('COMPOSED '+', '.join('Figure '+f for f in args.figures)+'; inspect final previews before delivery.')
