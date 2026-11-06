# Reproduce the three RNA-cohort analyses

This workflow contains the frozen extraction, association, independent verification and cohort-pooling scripts underlying the biological figures. The full input matrices must be downloaded from GEO. They are not part of this repository or the small software tutorial.

## Install and obtain the public files

From the repository root, using Python 3.11 or later:

```text
python -m pip install -r workflows/rna/requirements.txt
```

Create `raw/GSE234933`, `raw/GSE181919` and `raw/GSE310797`. Download the files below from each GEO series' Supplementary files section. Preserve the exact filenames. Links to NCBI's supplementary directories were checked during packaging; the data themselves are downloaded separately by the reproducing researcher.

| Cohort | Required downloads | Source |
|---|---|---|
| GSE234933 | `GSE234933_MGH_HNSCC_gex_raw_counts.tar.gz`; `GSE234933_MGH_HNSCC_cell_annotation.txt.gz`; `GSE234933_MGH_HNSCC_sample_annotation.txt.gz` | [GEO record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE234933), [download directory](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE234nnn/GSE234933/suppl/) |
| GSE181919 | `GSE181919_UMI_counts.txt.gz`; `GSE181919_Barcode_metadata.txt.gz` | [GEO record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE181919), [download directory](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE181nnn/GSE181919/suppl/) |
| GSE310797 | `GSE310797_RAW.tar` | [GEO record](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE310797), [download directory](https://ftp.ncbi.nlm.nih.gov/geo/series/GSE310nnn/GSE310797/suppl/) |

Extract only the expected gene-expression RDS files from the first archive and the expected PT1–PT16 count/cell-type files from the third. The helper below selects filenames from the frozen checksum list, writes them directly into each cohort directory, and never follows archive links or path traversal names. It verifies each selected file's checksum before accepting it. Existing identical files are retained; conflicting files cause an error.

```text
python workflows/rna/prepare_inputs.py extract GSE234933 raw/GSE234933/GSE234933_MGH_HNSCC_gex_raw_counts.tar.gz raw/GSE234933
python workflows/rna/prepare_inputs.py extract GSE310797 raw/GSE310797/GSE310797_RAW.tar raw/GSE310797
python workflows/rna/prepare_inputs.py verify GSE234933 raw/GSE234933
python workflows/rna/prepare_inputs.py verify GSE181919 raw/GSE181919
python workflows/rna/prepare_inputs.py verify GSE310797 raw/GSE310797
```

The exact expected filenames and SHA-256 values are in `analysis/expected_raw_sha256.json`: **54, 2 and 32 files**, respectively (88 total). The archive containers do not enter this count. If a public file changes, investigate the difference; do not replace its expected checksum merely to bypass the check. Input size and runtime are substantially larger than the tutorial; this full workflow is not presented as a ten-minute example.

## Extract full-gene myeloid counts

Run from the repository root:

```text
python -B workflows/rna/analysis/extract.py GSE234933 raw/GSE234933 private_cache
python -B workflows/rna/analysis/extract.py GSE181919 raw/GSE181919 private_cache
python -B workflows/rna/analysis/extract.py GSE310797 raw/GSE310797 private_cache
```

The cache retains all deposited gene rows for library-size calculations and the deposited cell annotations. Do not substitute log-transformed matrices or a highly-variable-gene subset. The primary analysis uses author-labelled myeloid cells, one specimen per donor, positive observed library totals and at least 30 retained cells. The fixed PT13 file has an incomplete final count row: it is retained among attempted donors and marked unavailable, not repaired or imputed.

The fixed 15-gene SPP1 signature can be independently checked from the bundled publisher XML:

```text
python workflows/rna/signature/verify_signature.py
```

## Fit and independently check the analyses

Use a new, empty output directory for each run. The frozen analysis checks the hashes of its own source, plan, input checksum list and vendor implementations before fitting.

```text
python -B workflows/rna/analysis/analyse.py run --cache private_cache --lock workflows/rna/analysis/analysis_lock.json --out outputs/rna
python -B workflows/rna/analysis/verify.py --cache private_cache --lock workflows/rna/analysis/analysis_lock.json --results outputs/rna --out outputs/rna_independent_checks.json
python -B workflows/rna/analysis/matched_anchors.py outputs/rna/patient_effects.tsv outputs/rna/anchor_matched_estimates.tsv
python -B workflows/rna/synthesis/pool.py --cohorts outputs/rna/cohort_estimates.tsv --out outputs/rna_pool
python workflows/rna/compare_results.py --analysis outputs/rna --pooled outputs/rna_pool
```

The last command compares all Figure 2/6 data fields with the saved result tables using numerical tolerance for floating-point values. It does not silently replace the figure inputs. Numerical failures should be investigated before adopting new output. Grouping, signature construction and model specifications remain in the frozen `analysis/PLAN.md`; retaining the original lock is necessary to verify source identity.

For equal-patient analysis, estimates, standard errors and intervals are in correlation units. Fisher REML/HKSJ estimates and endpoints are back-transformed, but its standard error and `estimate_z` remain on the Fisher scale. The two pooled rows retain those different meanings. The pooling script uses modified Hartung–Knapp mean intervals and three-cohort prediction intervals; it does not pool individual cell records.

## Verification scope

The original independent-check record is in `evidence/previous_independent_checks.json`. It verifies 503 available patient effects across 536 patient/analysis records and 34 cohort summary rows. These counts include sensitivity analyses and must not be represented as independent donors. Its original hashes and results are preserved; it is not evidence that packaging reran extraction.

This repository preparation checked input/source hashes, tested the new archive-preparation helper, refit the small three-cohort pooling calculation from saved cohort estimates, and regenerated the figures from a relocated directory. It did not download the full raw datasets or repeat the full raw extraction and cohort fitting. Instructions above enable that separate, larger check.
