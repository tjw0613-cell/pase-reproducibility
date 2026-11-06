"""Fit the locally locked common RNA analysis, using private gene-by-cell caches."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse,stats
from vendor.pase_weighted import summarize_patients

HERE=Path(__file__).resolve().parent
COHORTS=('GSE234933','GSE181919','GSE310797')
SIZES=(52,20,16)
KNOWN_LIST='78e84663d8dee89838a146cd1e71225f769879df3ddb700418cd53a71a5e0a0a'
def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def iso():return datetime.now(timezone.utc).isoformat()
def tsv(rows,dest):pd.DataFrame(rows).to_csv(dest,sep='\t',index=False,na_rep='NA',lineterminator='\n')

def freeze(cache,source,lock,axis):
    if lock.exists():raise FileExistsError(lock)
    assert sha(source)==KNOWN_LIST
    genes=source.read_text().splitlines();assert len(genes)==len(set(genes))==15
    assert not {'LILRB4','TREM2','CD68'}&set(genes)
    shared=set(genes)
    audit=[]
    for cohort,total in zip(COHORTS,SIZES):
        manifest=pd.read_csv(cache/cohort/'specimens.tsv',sep='\t')
        assert len(manifest)==total and manifest.specimen.is_unique
        for specimen,reason in zip(manifest.specimen,manifest.status):
            if reason!='ok':continue
            path=cache/cohort/specimen/'genes.txt'
            names=pd.Index(path.read_text(encoding='utf-8').upper().splitlines())
            multiplicity=names.value_counts()
            if any(multiplicity.get(g,0)!=1 for g in ('LILRB4','TREM2','CD68')):
                raise ValueError(f'A required anchor/covariate absent or ambiguous in {specimen}')
            for g in genes:
                n=int(multiplicity.get(g,0));audit.append(dict(cohort=cohort,specimen=specimen,gene=g,axis_occurrences=n))
                if n!=1:shared.discard(g)
    shared=[g for g in genes if g in shared]
    tsv(audit,axis);assert len(shared)>=.8*len(genes)
    files=[HERE/p for p in ('analyse.py','extract.py','PLAN.md','expected_raw_sha256.json','vendor/pase_weighted.py','vendor/external_core.py')]
    lock.write_text(json.dumps(dict(locked_utc=iso(),published_genes=genes,retained_genes=shared,
        signature_sha256=sha(source),axis_audit_sha256=sha(axis),files={p.relative_to(HERE).as_posix():sha(p) for p in files},
        interpretation='local revision-stage endpoint lock before outcome fitting'),indent=2)+'\n')

def score_data(folder,panel):
    m=sparse.load_npz(folder/'counts.npz');lib=np.asarray(m.sum(axis=1)).ravel()
    if np.any(lib<0) or np.any(lib>=2**53):raise ValueError('Invalid library')
    keep=lib>0;lib=lib[keep]
    genes=(folder/'genes.txt').read_text().upper().splitlines();genes_wanted=panel+['LILRB4','TREM2','CD68']
    ix=[genes.index(g) for g in genes_wanted]
    raw=m[keep][:,ix].toarray()
    val=np.log1p(raw*10000./lib[:,None])
    components=val[:,:len(panel)]
    if len(lib)>1:
        sd=components.std(axis=0,ddof=1)
        constant=(np.ptp(components,axis=0)==0)
        z=np.zeros_like(components)
        z[:,~constant]=(components[:,~constant]-components[:,~constant].mean(axis=0))/sd[~constant]
    else:
        constant=np.ones(len(panel),dtype=bool);z=np.zeros_like(components)
    return dict(LILRB4=val[:,-3],TREM2=val[:,-2],CD68=val[:,-1],y=z.mean(axis=1),
        depth=np.log1p(lib),gate=(raw[:,:len(panel)]>0).sum(axis=1)>=2,
        n_constant=int(constant.sum()),constant_genes=','.join(np.asarray(panel)[constant]))

def patient(dat,mode,record):
    if dat is None:return dict(record,n_complete=None,design_rank=None,r=None),None
    selected=dat['gate'] if mode=='detection_gate' else np.ones(len(dat['y']),bool)
    x=dat['TREM2' if mode=='trem2' else 'LILRB4'][selected];y=dat['y'][selected]
    n=len(x);out=dict(record,n_complete=n,design_rank=None,r=None,n_constant_signature=dat["n_constant"],constant_genes=dat['constant_genes'])
    if n<30:return dict(out,status='below_cell_minimum'),None
    nuisance=[] if mode=='unadjusted' else ['depth','CD68'] if mode=='depth_cd68' else ['depth']
    cols=[np.ones(n)]
    for k in nuisance:
        a=dat[k][selected];scale=a.std(ddof=1)
        if scale>1e-12:cols.append((a-a.mean())/scale)
    design=np.column_stack(cols);rank=np.linalg.matrix_rank(design);out['design_rank']=int(rank)
    if n-rank<3:return dict(out,status='insufficient_residual_df'),None
    expr=np.column_stack((x,y)); resid=expr-design@np.linalg.lstsq(design,expr,rcond=None)[0]
    residual_norm=np.linalg.norm(resid,axis=0)
    if np.any(residual_norm<=1e-10*np.maximum(1,np.linalg.norm(expr,axis=0))):
        return dict(out,status='degenerate_residual'),None
    r=np.dot(resid[:,0],resid[:,1])/np.prod(residual_norm)
    return dict(out,r=float(r),status='ok'),(expr,resid)

def fit_rows(rows,n_multiplier=None):
    records=[dict(patient_id=z['donor'],r=z['r'],n=(z['n_complete'] or 0)*(n_multiplier or {}).get(z['donor'],1),
                  design_rank=z['design_rank'],eligible=z['status']=='ok') for z in rows]
    return summarize_patients(records)

def summaries(cohort,group,rows,fit):
    out=[]
    for method in ('equal_t','reml_hksj'):
        rf=fit['equal_r'] if method=='equal_t' else fit['reml']
        iv=rf if method=='equal_t' else rf['hk']
        elig='equal_eligible' if method=='equal_t' else 'fisher_eligible'
        pts=[p for p in fit['patients'] if p[elig]]
        out.append(dict(cohort=cohort,analysis=group,method=method,attempted=len(rows),eligible=rf['J'],estimate=rf['estimate'],
            se=iv['se'],se_scale='r' if method=='equal_t' else 'fisher_z',low=iv['ci_low'],high=iv['ci_high'],
            estimate_z=rf.get('estimate_z'),tau2_z=rf.get('tau2'),status=iv['status'],positive=sum(p['r']>0 for p in pts),
            negative=sum(p['r']<0 for p in pts),zero=sum(p['r']==0 for p in pts),
            median_descriptive=np.median([p['r'] for p in pts]) if pts else None))
    return out

def correlation(v):
    """Pearson from within-person raw sums: N, X, Y, XX, YY, XY."""
    n,x,y,xx,yy,xy=v
    return (xy-x*y/n)/np.sqrt((xx-x*x/n)*(yy-y*y/n))
def sufficient(xy):
    x,y=xy.T
    return np.array([len(x),x.sum(),y.sum(),x@x,y@y,x@y])

def influence(cohort,rows,moments):
    subset=[z for z in rows if z['status']=='ok'];ids=[z['donor'] for z in subset]
    largest=sorted(subset,key=lambda z:(-z['n_complete'],z['donor']))[0]['donor']
    out=[]
    for tag,omitted,mult in [('original',None,1),('largest_tenfold',None,10),*[('omit_one',d,1) for d in ids]]:
        rr=[z for z in subset if z['donor']!=omitted]
        copies={z['donor']:(mult if z['donor']==largest else 1) for z in rr}
        raw,resid=[sum(moments[z['donor']][idx]*copies[z['donor']] for z in rr) for idx in (0,1)]
        fit=fit_rows(rr,copies)
        out.append(dict(cohort=cohort,scenario=tag,omitted=omitted,largest_donor=largest,n_cells=int(raw[0]),eligible=len(rr),
            largest_cell_share=0 if omitted==largest else moments[largest][0][0]*mult/raw[0],
            pooled_Pearson=correlation(raw),stacked_residual_Pearson=correlation(resid),
            equal_t=fit['equal_r']['estimate'],reml_hksj=fit['reml']['estimate']))
    return out

def run(cache,lock,out):
    spec=json.loads(lock.read_text());panel=spec['retained_genes'];assert len(panel)>=12
    for path,digest in spec['files'].items():assert sha(HERE/path)==digest
    if out.exists():raise FileExistsError(out)
    out.mkdir(parents=True)
    all_patient=[];all_summary=[];all_weight=[];all_pooled=[];paired=[]
    for cohort in COHORTS:
        baseline=pd.read_csv(cache/cohort/'specimens.tsv',sep='\t')
        data={}
        for _,row in baseline.iterrows():
            data[row.specimen]=None if row.status!='ok' else score_data(cache/cohort/row.specimen,panel)
        modes=['primary','detection_gate','unadjusted','depth_cd68','trem2']
        if cohort=='GSE234933':modes+=['later_recurrence','exclude_recurrence_donor']
        anchors={}
        for mode in modes:
            skip={'HN23'} if mode=='later_recurrence' else {'HN23','HN45'} if mode=='exclude_recurrence_donor' else {'HN45'}
            rows=[];moments={}
            for _,row in baseline.iterrows():
                if cohort=='GSE234933' and row.specimen in skip:continue
                rec=dict(cohort=cohort,analysis=mode,specimen=row.specimen,donor=row.donor,status=row.status)
                p,v=patient(data[row.specimen],mode,rec);rows.append(p)
                if v is not None:moments[p['donor']]=tuple(sufficient(a) for a in v)
            assert len({r['donor'] for r in rows})==len(rows)
            fit=fit_rows(rows);all_patient.extend(rows);all_summary.extend(summaries(cohort,mode,rows,fit))
            for p in fit['patients']:
                all_weight.append(dict(cohort=cohort,analysis=mode,donor=p['patient_id'],equal_eligible=p['equal_eligible'],fisher_eligible=p['fisher_eligible'],
                    equal_weight=1/fit['equal_r']['J'] if p['equal_eligible'] else 0,reml_weight=fit['reml'].get('weights',{}).get(p['patient_id'],0)))
            if mode in ('primary','trem2'):anchors[mode]={p['donor']:p['r'] for p in rows if p['status']=='ok'}
            if mode=='primary':all_pooled.extend(influence(cohort,rows,moments))
        common=sorted(set(anchors['primary'])&set(anchors['trem2']))
        d=np.array([anchors['primary'][k]-anchors['trem2'][k] for k in common])
        se=d.std(ddof=1)/np.sqrt(len(d));margin=stats.t.ppf(.975,len(d)-1)*se
        paired.append(dict(cohort=cohort,shared_eligible=len(d),LILRB4_mean=np.mean([anchors['primary'][k] for k in common]),
            TREM2_mean=np.mean([anchors['trem2'][k] for k in common]),difference=d.mean(),low=d.mean()-margin,high=d.mean()+margin))
    for name,rows in [('patient_effects',all_patient),('cohort_estimates',all_summary),('patient_weights',all_weight),('pooling_influence',all_pooled),('anchor_comparison',paired)]:
        tsv(rows,out/(name+'.tsv'))
    (out/'run.json').write_text(json.dumps(dict(completed_utc=iso(),lock_sha256=sha(lock),
        outputs={f.name:sha(f) for f in sorted(out.glob('*.tsv'))}),indent=2)+'\n')

if __name__=='__main__':
    arg=argparse.ArgumentParser();arg.add_argument('action',choices=['freeze','run']);arg.add_argument('--cache',required=True,type=Path);arg.add_argument('--lock',required=True,type=Path)
    arg.add_argument('--list',type=Path);arg.add_argument('--axis',type=Path);arg.add_argument('--out',type=Path)
    args=arg.parse_args()
    if args.action=='freeze':freeze(args.cache,args.list,args.lock,args.axis)
    else:run(args.cache,args.lock,args.out)
