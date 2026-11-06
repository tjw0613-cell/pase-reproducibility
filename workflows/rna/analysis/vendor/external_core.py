"""Strict streaming parser and patient-unit checks for original GEO matrices."""
from __future__ import annotations
import gzip
import re
import numpy as np
from scipy.stats import binom


def normalize_barcode(value):
    match=re.fullmatch(r'([ACGTN]+)[.-](\d+)',str(value))
    if not match:
        raise ValueError(f'Unexpected barcode syntax: {value!r}')
    return match[1]+'-'+match[2]


def stream_counts(path,wanted):
    raw={}; genes=set()
    with gzip.open(path,'rt',encoding='utf-8') as handle:
        cells=[normalize_barcode(x) for x in handle.readline().rstrip('\r\n').split('\t')]
        if len(set(cells))!=len(cells):
            raise ValueError('Duplicate normalized barcodes')
        lib=np.zeros(len(cells),dtype=np.float64)
        for i,line in enumerate(handle,1):
            gene,sep,payload=line.partition('\t')
            if not sep or not gene or gene in genes:
                raise ValueError(f'Missing or duplicate gene at row {i}: {gene}')
            genes.add(gene)
            # Deliberately accept integer text only; catches partially parsed last tokens.
            if re.search(r'[^0-9\t\r\n]',payload):
                raise ValueError(f'Non-integer/nonfinite/negative count at gene {gene}')
            vals=np.fromstring(payload,sep='\t',dtype=np.float64)
            if len(vals)!=len(cells) or payload.rstrip('\r\n').count('\t')!=len(cells)-1:
                raise ValueError(f'Wrong row width at gene {gene}')
            if not np.all(np.isfinite(vals)) or np.any(vals<0) or np.any(vals>=2**53):
                raise ValueError(f'Invalid or inexact integer count at gene {gene}')
            lib+=vals
            if gene in wanted:
                raw[gene]=vals
            if i%5000==0:
                print(f'Parsed {i} complete gene rows',flush=True)
    if not genes or np.any(lib<=0) or np.any(lib>=2**53):
        raise ValueError('Empty matrix, zero library or inexact integer library')
    if set(wanted)-raw.keys():
        raise ValueError('Missing required genes: '+','.join(sorted(set(wanted)-raw.keys())))
    return raw,lib,cells,{'n_cells':len(cells),'n_genes':len(genes),'n_retained_genes':len(raw),
        'library_min':float(lib.min()),'library_max':float(lib.max()),
        'library_sum':float(lib.sum()),'integer_nonnegative_counts':True,
        'unique_genes':True,'unique_normalized_barcodes':True,'gzip_eof_crc_checked':True}


def primary_patient_map(anno):
    columns=['patient.id','sample.id','tissue.type','subsite','hpv']
    if anno[columns].isna().any().any():
        raise ValueError('Missing core patient metadata')
    m=anno.loc[anno['tissue.type'].eq('CA'),columns].drop_duplicates()
    if m['patient.id'].duplicated().any() or m['sample.id'].duplicated().any():
        raise ValueError('Primary specimen/patient mapping not one-to-one or inconsistent metadata')
    return m.sort_values('sample.id').reset_index(drop=True)


def exact_median_interval(values):
    """Conservative order-statistic 95% median CI; independence assumed."""
    v=np.sort(np.asarray(values,float)); n=len(v)
    valid=[k for k in range(1,n//2+1) if binom.cdf(k-1,n,.5)<=.025]
    if not valid:
        return None,None,None
    k=max(valid)
    return float(v[k-1]),float(v[n-k]),float(1-2*binom.cdf(k-1,n,.5))
