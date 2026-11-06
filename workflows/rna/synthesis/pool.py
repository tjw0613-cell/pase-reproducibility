"""Pool primary cohort-level estimates separately on their declared scales."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy import stats

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"analysis/vendor"))
from pase_weighted import _reml_tau2

def synthesise(y, se, fisher):
    y,se=np.asarray(y,dtype=float),np.asarray(se,dtype=float)
    k=len(y)
    if k<2 or not np.isfinite(y+se).all() or np.any(se<=0):
        raise ValueError("At least two eligible cohort estimates with positive SE are required.")
    v=se**2
    common=np.average(y,weights=1/v)
    q0=float(np.sum((y-common)**2/v))
    tau2=_reml_tau2(y,v)
    w=1/(tau2+v)
    u=np.average(y,weights=w)
    q=float(np.dot(w,(y-u)**2)/(k-1))
    s=np.sqrt(max(1.,q)/w.sum())
    ci=stats.t.isf(.025,k-1)*s
    transform=np.tanh if fisher else float
    d=dict(k=k,scale="Fisher z" if fisher else "correlation",estimate=transform(u),
           low=transform(u-ci),high=transform(u+ci),mean_native=u,se_native=s,
           tau2=tau2,Q=q0,Q_df=k-1,I2_percent=100*max(0.,1-(k-1)/q0) if q0 else 0.,
           hk_factor=q,pi_df=None,pi_low=None,pi_high=None)
    if k>=3:
        delta=stats.t.isf(.025,k-2)*np.sqrt(tau2+s*s)
        d.update(pi_df=k-2,pi_low=transform(u-delta),pi_high=transform(u+delta))
    return d,w/w.sum()

def write(name,rows,directory):
    with (directory/name).open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter="\t");w.writeheader();w.writerows(rows)

def run(src, dest):
    with src.open(encoding="utf-8-sig",newline="") as f: all_rows=list(csv.DictReader(f,delimiter="\t"))
    pooled=[];weights=[];omit=[]
    for method in ("equal_t","reml_hksj"):
        series=[r for r in all_rows if r["analysis"]=="primary" and r["method"]==method]
        if len(series)!=3 or {r["cohort"] for r in series}!={"GSE234933","GSE181919","GSE310797"}:
            raise ValueError(f"Missing/duplicate primary cohort or method: {method}")
        series=sorted(series,key=lambda r:("GSE234933","GSE181919","GSE310797").index(r["cohort"]))
        key="estimate_z" if method=="reml_hksj" else "estimate"
        y=np.array([float(r[key]) for r in series]);se=np.array([float(r["se"]) for r in series])
        answer,w=synthesise(y,se,method=="reml_hksj");pooled.append(dict(method=method,**answer))
        for i,row in enumerate(series):
            weights.append(dict(method=method,cohort=row["cohort"],weight=w[i]))
            keep=np.arange(3)!=i;other,_=synthesise(y[keep],se[keep],method=="reml_hksj")
            omit.append(dict(method=method,omitted=row["cohort"],**other))
    dest.mkdir(parents=True,exist_ok=True)
    write("pooled.tsv",pooled,dest);write("weights.tsv",weights,dest);write("leave_one_cohort_out.tsv",omit,dest)
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [src, Path(__file__),HERE/"PLAN.md",*(dest/n for n in ("pooled.tsv","weights.tsv","leave_one_cohort_out.tsv"))]}
    (dest/"hashes.json").write_text(json.dumps(hashes,indent=2)+"\n",encoding="utf-8")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--cohorts",type=Path,required=True);p.add_argument("--out",type=Path,required=True)
    args=p.parse_args();run(args.cohorts,args.out)
