"""Independently verify donor effects, cohort estimates, eligibility and matched subsets."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import sparse, optimize, stats

cli=argparse.ArgumentParser();cli.add_argument('--cache',type=Path,required=True);cli.add_argument('--lock',type=Path,required=True);cli.add_argument('--results',type=Path,required=True);cli.add_argument('--out',type=Path,required=True)
args=cli.parse_args()
panel=json.loads(args.lock.read_text())['retained_genes']
df=pd.read_csv(args.results/'patient_effects.tsv',sep='\t'); outcome=pd.read_csv(args.results/'cohort_estimates.tsv',sep='\t')
def close(a,b,tol=1e-10): np.testing.assert_allclose(a,b,rtol=tol,atol=tol)
n_checked=0; max_patient_error=0
for (cohort,specimen),records in df.groupby(['cohort','specimen']):
    folder=args.cache/cohort/specimen
    if records.status.eq('source_incomplete_count_row').all():
        assert cohort=='GSE310797' and specimen=='PT13' and records.r.isna().all();continue
    mat=sparse.load_npz(folder/'counts.npz').tocsr()
    names=(folder/'genes.txt').read_text().upper().splitlines()
    ix=[names.index(g) for g in ['LILRB4','TREM2','CD68',*panel]]
    library=np.asarray(mat.sum(axis=1)).ravel();keep=library>0;library=library[keep]
    raw=mat[keep][:,ix].toarray()
    expr=np.log1p(raw.astype(float)/library[:,None]*10000)
    y=np.zeros(len(library))
    for col in expr[:,3:].T:
        if len(col)>1 and np.ptp(col)>0:y+=(col-col.mean())/col.std(ddof=1)/len(panel)
    for rec in records.itertuples():
        gate=np.count_nonzero(raw[:,3:],axis=1)>=2 if rec.analysis=='detection_gate' else np.ones(len(y),bool)
        assert rec.n_complete==gate.sum()
        if len(y[gate])<30:
            assert rec.status=='below_cell_minimum';continue
        x=expr[gate,1 if rec.analysis=='trem2' else 0];yg=y[gate];nuis=[]
        if rec.analysis!='unadjusted':nuis.append(np.log1p(library[gate]))
        if rec.analysis=='depth_cd68':nuis.append(expr[gate,2])
        Z=np.column_stack([np.ones(len(x)),*[v for v in nuis if np.std(v,ddof=1)>1e-12]])
        rank=np.linalg.matrix_rank(Z);assert rank==rec.design_rank
        Q=np.linalg.svd(Z,full_matrices=False)[0][:,:rank]
        a=x-Q@(Q.T@x);b=yg-Q@(Q.T@yg)
        if min(np.linalg.norm(a)/max(1,np.linalg.norm(x)),np.linalg.norm(b)/max(1,np.linalg.norm(yg)))<=1e-10:
            assert rec.status=='degenerate_residual';continue
        v=float(np.corrcoef(a,b)[0,1]);assert rec.status=='ok'
        close(v,rec.r);max_patient_error=max(max_patient_error,abs(v-rec.r));n_checked+=1

max_summary_error=0
for z in outcome.itertuples():
    rows=df[(df.cohort==z.cohort)&(df.analysis==z.analysis)]
    assert rows.donor.nunique()==z.attempted==len(rows)
    q=rows[rows.r.notna()].copy();r=q.r.to_numpy()
    if z.method=='equal_t':
        estimate=r.mean();se=stats.sem(r);lo,hi=stats.t.interval(.95,len(r)-1,loc=estimate,scale=se)
    else:
        q=q[q.r.abs()<1];r=q.r.to_numpy()
        d=1/(q.n_complete.to_numpy()-q.design_rank.to_numpy()-2)
        y=np.arctanh(r)
        def nll(tau):
            var=d+tau;w=1/var;mu=np.average(y,weights=w)
            return np.log(var).sum()+np.log(w.sum())+sum(w*(y-mu)**2)
        hi_search=max(1.0,np.var(y,ddof=1)*5)
        sol=optimize.minimize_scalar(nll,bounds=(0,hi_search),method='bounded',options={'xatol':1e-15})
        tau=0.0 if nll(0)<=nll(sol.x) else sol.x
        w=1/(d+tau);mu=np.average(y,weights=w)
        se=np.sqrt(sum(w*(y-mu)**2)/((len(r)-1)*w.sum()))
        lo,hi=np.tanh(stats.t.interval(.95,len(r)-1,loc=mu,scale=se));estimate=np.tanh(mu)
        close(tau,z.tau2_z,1e-7)
    assert z.eligible==len(r) and z.positive==(r>0).sum()
    for a,b in [(estimate,z.estimate),(se,z.se),(lo,z.low),(hi,z.high)]:
        close(a,b,1e-7);max_summary_error=max(max_summary_error,abs(a-b))

pool=pd.read_csv(args.results/'pooling_influence.tsv',sep='\t')
for cohort,g in pool.groupby('cohort'):
    base=g[g.scenario=='original'].iloc[0];boost=g[g.scenario=='largest_tenfold'].iloc[0]
    assert int(base.eligible)==int(boost.eligible)==len(g[g.scenario=='omit_one'])
    close(base.equal_t,boost.equal_t)
    patient=df[(df.cohort==cohort)&(df.analysis=='primary')&df.r.notna()]
    largest=patient.sort_values(['n_complete','donor'],ascending=[False,True]).iloc[0]
    assert largest.donor==base.largest_donor and boost.n_cells-base.n_cells==9*largest.n_complete
    for row in g[g.scenario=='omit_one'].itertuples():
        close(row.equal_t,patient.loc[patient.donor!=row.omitted,'r'].mean())
paired=pd.read_csv(args.results/'anchor_comparison.tsv',sep='\t')
for p in paired.itertuples():
    g=df[(df.cohort==p.cohort)&df.analysis.isin(['primary','trem2'])].pivot(index='donor',columns='analysis',values='r').dropna()
    assert len(g)==p.shared_eligible
    close(np.mean(g.primary-g.trem2),p.difference)
report=dict(patient_rows=len(df),available_patient_effects_verified=n_checked,max_patient_absolute_error=max_patient_error,
    cohort_summary_rows=len(outcome),max_summary_absolute_error=max_summary_error,paired_anchor_checks=len(paired),
    leave_one_out_and_tenfold_checked=True,source_failure='PT13',lock_sha256=hashlib.sha256(args.lock.read_bytes()).hexdigest())
args.out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
