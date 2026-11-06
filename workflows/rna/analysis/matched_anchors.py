"""Supplement. Refit both anchors on exactly the same patient set for each method."""
import argparse
from pathlib import Path
import pandas as pd
from analyse import fit_rows,summaries,tsv

cli=argparse.ArgumentParser()
cli.add_argument('patient_effects',type=Path)
cli.add_argument('output',type=Path)
args=cli.parse_args()
patient=pd.read_csv(args.patient_effects,sep='\t')
outputs=[]
for cohort,df in patient[patient.analysis.isin(['primary','trem2'])].groupby('cohort'):
    rows={a:d.to_dict('records') for a,d in df.groupby('analysis')}
    rawfits={a:fit_rows(rr) for a,rr in rows.items()}
    for method,flag in [('equal_t','equal_eligible'),('reml_hksj','fisher_eligible')]:
        sets=[set(r['patient_id'] for r in fit['patients'] if r[flag]) for fit in rawfits.values()]
        common=sets[0]&sets[1]
        for anchor,rr in rows.items():
            selected=[r for r in rr if r['donor'] in common];fit=fit_rows(selected)
            s=next(s for s in summaries(cohort,anchor,selected,fit) if s['method']==method)
            assert s['eligible']==len(common)
            s['before_intersection']=len(rr);s['attempted']=len(rr);s['common_set_eligible']=len(common)
            outputs.append(s)
tsv(outputs,args.output)
