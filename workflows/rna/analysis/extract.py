"""Create private, full-gene, broad-myeloid count caches from the deposited files."""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from scipy import sparse
from vendor.external_core import normalize_barcode,primary_patient_map

HERE=Path(__file__).resolve().parent
def sha(path):
    with path.open('rb') as h:return hashlib.file_digest(h,'sha256').hexdigest()

def write_sample(out,sample,donor,counts,genes,barcodes,status='ok'):
    folder=out/sample;folder.mkdir(parents=True,exist_ok=True)
    if counts is not None:
        counts=counts.tocsr()
        if counts.shape!=(len(barcodes),len(genes)) or len(set(barcodes))!=len(barcodes):
            raise ValueError('Matrix/barcode mismatch: '+sample)
        if not np.all(np.isfinite(counts.data)&(counts.data>=0)&(counts.data==np.rint(counts.data))):
            raise ValueError('Invalid counts: '+sample)
        if np.max(counts.data,initial=0)>2**31-1:raise ValueError('Count overflow')
        sparse.save_npz(folder/'counts.npz',counts.astype('int32'))
        (folder/'genes.txt').write_text('\n'.join(genes)+'\n',encoding='utf-8')
        (folder/'barcodes.txt').write_text('\n'.join(barcodes),encoding='utf-8')
    row=dict(specimen=sample,donor=donor,status=status,annotated_cells=None if counts is None else counts.shape[0],
             positive_library_cells=None if counts is None else int((np.asarray(counts.sum(axis=1)).ravel()>0).sum()))
    (folder/'qc.json').write_text(json.dumps(row,indent=2)+'\n')
    return row

def text_matrix(path,select_fn,geo181=False):
    with gzip.open(path,'rb') as f:
        header=f.readline().decode().rstrip('\r\n').split('\t')
        barcodes=[normalize_barcode(x) for x in header] if geo181 else header[1:]
        if len(barcodes)!=len(set(barcodes)):raise ValueError('Duplicate count barcode')
        selected=select_fn(barcodes)
        pos=np.flatnonzero(selected)
        genes=[];cols=[];values=[];ptr=[0]
        for line in f:
            name,raw=line.rstrip(b'\r\n').split(b'\t',1)
            if raw.count(b'\t')+1!=len(barcodes):raise ValueError('Malformed count row: '+str(name))
            vals=np.fromstring(raw,dtype=np.int64,sep='\t')
            if len(vals)!=len(barcodes) or np.any(vals<0):raise ValueError('Invalid integer row')
            vals=vals[pos];idx=np.flatnonzero(vals)
            cols.append(idx.astype(np.int32));values.append(vals[idx]);ptr.append(ptr[-1]+len(idx))
            genes.append(name.decode())
    mat=sparse.csr_matrix((np.concatenate(values),np.concatenate(cols),ptr),shape=(len(genes),len(pos))).T.tocsr()
    return mat,genes,np.asarray(barcodes)[pos]

def gse181919(src,out):
    anno=pd.read_csv(src/'GSE181919_Barcode_metadata.txt.gz',sep='\t',index_col=0)
    anno.index=anno.index.map(normalize_barcode)
    patients=primary_patient_map(anno)
    assert anno.index.is_unique and len(patients)==20
    def select(barcodes):
        if set(barcodes)!=set(anno.index):raise ValueError('Incomplete deposited annotation')
        a=anno.loc[barcodes]
        return (a['sample.id'].isin(patients['sample.id'])&a['cell.type'].isin(['Macrophages','Dendritic.cells'])).to_numpy()
    mat,genes,barcodes=text_matrix(src/'GSE181919_UMI_counts.txt.gz', select,True)
    a=anno.loc[barcodes];outrows=[]
    for donor,sample in patients[['patient.id','sample.id']].itertuples(index=False,name=None):
        sel=a['sample.id'].eq(sample).to_numpy();outrows.append(write_sample(out,sample,donor,mat[sel],genes,barcodes[sel]))
    return outrows

def gse234933(src,out):
    import rdata
    anno=pd.read_csv(src/'GSE234933_MGH_HNSCC_cell_annotation.txt.gz',sep='\t',dtype=str)
    meta=pd.read_csv(src/'GSE234933_MGH_HNSCC_sample_annotation.txt.gz',sep='\t',dtype=str)
    mats={f.name.removesuffix('_gex_raw_counts.rds'):f for f in src.glob('*_gex_raw_counts.rds')}
    if len(mats)!=52 or set(mats)!=set(meta.Sample) or meta.Sample.duplicated().any():raise ValueError('Missing specimen')
    outrows=[]
    for name,path in sorted(mats.items()):
        donor='HN23_HN45' if name in ('HN23','HN45') else name
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore',message='Missing constructor for R class "dgCMatrix".*')
            obj=rdata.read_rds(path)
        mat=sparse.csc_matrix((np.asarray(obj.x),np.asarray(obj.i),np.asarray(obj.p)),shape=tuple(obj.Dim))
        genes,barcodes=(np.asarray(v,dtype=str) for v in obj.Dimnames)
        a=anno[anno['sample']==name]
        if not a.sample_barcode.is_unique or len(barcodes)!=len(set(barcodes)) or set(a.sample_barcode)-set(barcodes): raise ValueError('Unmatched annotation '+name)
        keep=a.loc[a.subclustering=='Myeloid cells','sample_barcode'].tolist();idx=pd.Index(barcodes).get_indexer(keep)
        outrows.append(write_sample(out,name,donor,mat[:,idx].T,genes,keep))
        print(name,len(idx),flush=True)
    return outrows

def gse310797(src,out):
    paths=sorted(p for p in src.glob('GSM*_PT[0-9]*_count.txt.gz') if '_SP_' not in p.name);assert len(paths)==16
    outrows=[]
    for path in paths:
        sample=path.name.removesuffix('_count.txt.gz').split('_')[-1]
        if sample=='PT13':
            assert sha(path)=='8554e03b1f986c710c2bbe2077ad313fc2af8a2441ad15adcabdbf04e8cae306'
            outrows.append(write_sample(out,sample,sample,None,[],[],status='source_incomplete_count_row'));continue
        a=pd.read_csv(path.with_name(path.name.replace('count.txt.gz','celltype.txt.gz')),sep='\t',index_col=0)
        if not a.index.is_unique or len(a.columns)!=1:raise ValueError('Invalid annotation '+sample)
        def select(barcodes):
            if set(a.index)!=set(barcodes):raise ValueError('Incomplete annotated barcode overlap '+sample)
            return a.loc[barcodes].iloc[:,0].eq('Myeloid cells').to_numpy()
        mat,genes,bcs=text_matrix(path,select)
        outrows.append(write_sample(out,sample,sample,mat,genes,bcs))
        print(sample,len(bcs),flush=True)
    return outrows

if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('cohort',choices=['GSE181919','GSE234933','GSE310797']);cli.add_argument('source',type=Path);cli.add_argument('cache',type=Path)
    args=cli.parse_args();expected=json.loads((HERE/'expected_raw_sha256.json').read_text())[args.cohort]
    for name,digest in expected.items():
        if sha(args.source/name)!=digest:raise ValueError('Source changed: '+name)
    out=args.cache/args.cohort;out.mkdir(parents=True,exist_ok=True)
    rows=globals()[args.cohort.lower()](args.source,out)
    pd.DataFrame(rows).to_csv(out/'specimens.tsv',sep='\t',index=False)
