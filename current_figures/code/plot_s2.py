"""Regenerate Figure S2 from the checked 18-row source table, without refitting."""
from pathlib import Path
import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from font_policy import resolve_fonts
FONT_INFO=resolve_fonts()
ROOT=Path(__file__).resolve().parents[1]
F=Path(os.environ['PASE_FIGURE_OUTPUT_DIR']).resolve()
frame=pd.read_csv(ROOT/'inputs/native_allocation_comparison.tsv', sep='\t')
if len(frame)!=18 or frame.duplicated(['allocation','scenario','method']).any():
    raise ValueError('Expected 18 unique allocation/scenario/method rows')
if not (frame.attempted==500).all():
    raise ValueError('The final native benchmark uses 500 attempts per scenario/allocation')
plt.rcParams.update({'font.family':FONT_INFO['family'],'font.size':8,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none'})
fig,axs=plt.subplots(1,3,figsize=(180/25.4,72/25.4),sharey=True)
methods=['pase_equal_t','pase_reml_hksj','memento_conditional_mean'];names=['Equal-patient t','REML–HKSJ','memento']
for k,(ax,sc,title) in enumerate(zip(axs,['global_null','fixed_positive','heterogeneous_positive'],['Generating null','Fixed positive','Heterogeneous positive'])):
    for allocation,offset,fill in [('Equal (80)',.12,'white'),('Unequal (20–260)',-.12,'#494949')]:
        for y,m in zip([2,1,0],methods):
            z=frame[(frame.allocation==allocation)&(frame.scenario==sc)&(frame.method==m)].iloc[0]
            ax.errorbar(z.rate*100,y+offset,xerr=[[100*(z.rate-z.Wilson_low)],[100*(z.Wilson_high-z.rate)]],fmt='o',ms=4,mec='#494949',mfc=fill,color='#494949',elinewidth=.9,capsize=2,zorder=3)
    ax.set_title(title,fontsize=8,pad=9);ax.text(-.12,1.11,chr(65+k),transform=ax.transAxes,weight='bold',fontsize=10,color='black')
    ax.set_yticks([2,1,0],names);ax.set_ylim(-.45,2.45);ax.set_xlabel('Rejection rate (%)');ax.tick_params(length=3)
    ax.grid(axis='x',color='#E6E6E6',lw=.5,zorder=0)
    if k==0:ax.set_xlim(-.4,10.4);ax.set_xticks([0,5,10]);ax.axvline(5,ls='--',color='#888888',lw=.7)
    else:ax.set_xlim(-2,102);ax.set_xticks([0,50,100])
fig.legend(handles=[Line2D([],[],marker='o',mfc='white',mec='#494949',color='#494949',lw=.8,label='Equal: 80 cells'),Line2D([],[],marker='o',mfc='#494949',mec='#494949',color='#494949',lw=.8,label='Unequal: 20–260 cells')],loc='upper center',bbox_to_anchor=(.55,1.0),ncol=2,frameon=False,fontsize=8)
fig.subplots_adjust(left=.19,right=.985,bottom=.21,top=.71,wspace=.34)
for ext in ['pdf','svg','png','tiff']:fig.savefig(F/f'Figure_S2.{ext}',dpi=600,facecolor='white',metadata={'Creator':'PASE authors'} if ext=='pdf' else None)
plt.close(fig)
