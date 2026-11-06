# Figure and source map

All paths below are relative to this repository. Table bytes are checked by `source_manifest.json`. Figures 1, 2 and 5 share drawing utilities, but each public `scripts/figN.py` entry point produces only its corresponding figure.

| Panel | Exact input | Displayed quantity and boundary |
|---|---|---|
| 1A–C | `scripts/_drawings.py`, function `fig1` | Conceptual routes and three aggregation targets. The 9/4/2 drawn cells are illustrative, not observed sample counts. Empirical Bayes estimates individuals, not a group-test result. |
| 2A | `data/gaussian/comparison.csv` | Select `global_null`, both allocations, and pooled Pearson, pooled Spearman and equal-patient t. Rejection rates among available tests, with stored pointwise Wilson intervals, 2,000 datasets per allocation and eight donors. |
| 2B | `data/biology/pooling_influence.tsv` | `original` versus `largest_tenfold` for three cohorts; the same processed cells and donor IDs are retained. The largest donor has ten copies total. This changes leverage without new biological observations. |
| 3 | No formal output exists | Planned coverage and type-I-error heatmaps. Exit 2, no plot. |
| 4 | No formal output exists | Planned bias, efficiency and selection comparisons. Exit 2, no plot. |
| 5A | `data/gaussian/comparison.csv` | Native rejection rates for six methods, two allocations and three scenarios. Displayed percentages use decimal half-up rounding to one decimal. Positive scenarios have different targets and are not a common-target power ranking. |
| 5B | `data/controls/positive_reference_summary.tsv`, `shuffle_summary.tsv`, `memento_tests.tsv`, `sc_C1QA_C1QB.csv`, `sc_HLA-DRA_CD74.csv`, `sc_MS4A7_CD14.csv`, `sc_RPLP0_RPL13A.csv` | Four selected reference pairs in 19 GSE181919 donors; a call requires positive estimate and nominal two-sided P < 0.05. scCOSMiX has one usable fit out of four attempted pairs. The shuffle column counts rejections among 999 within-donor LILRB4–MMP14 permutations for methods with that test. A within-donor shuffle leaves donor aggregate values unchanged. |
| 5C | `data/resources/summary.tsv` | Single-pair runtime and peak process-tree memory: 20 donors, 32 genes, 10,000/100,000/1,000,000 cells. Medians of three successful runs, or one censored scCOSMiX attempt. PASE computes three summaries; memento computes moments without bootstrap testing. Workloads are not identical. |
| 5D | `data/count_pilot/summary.tsv`, `sc_summary.tsv` | Completed balanced eight-donor count pilot. Rejected/usable fits, 100 attempts for PASE and memento; 12 scCOSMiX attempts. This pilot is separate from the unrun unified simulation. |
| 6A | `data/biology/cohort_estimates.tsv`, `pooled.tsv` | Primary cohort equal means and t intervals, plus Fisher REML means and HKSJ intervals. Cohort pooling uses separate scales and modified Hartung–Knapp mean intervals. Dashed lines are three-cohort prediction intervals. |
| 6B | `data/biology/cohort_estimates.tsv` | Equal-patient mean and t intervals for depth adjustment, a detection gate, no adjustment and depth plus CD68. GSE181919 has 18 eligible donors under the gate and 19 in the primary analysis. |
| 6C | `data/biology/pooling_influence.tsv` | Original pooled-cell, stacked-residual, equal-patient and Fisher REML estimates, each with its native target. |
| 6D | `scripts/fig6.py` | Reporting policy, not an empirically validated patient-count threshold. J ≥ 2 is a mathematical calculability condition; study-specific floors and uncertainty settings remain explicit. |

## Gaussian controls

The retrospective continuous-data controls use independent gene-specific donor shifts and independent within-donor innovations under the global null. Allocations are 80 cells per donor or lognormal yields clipped to 20–260. Fixed associations use rho = 0.2; heterogeneous associations independently assign rho = −0.05 or 0.45 with equal probability. All three scenarios reuse original innovations. The six allocation/scenario columns should not be counted as independent simulated datasets. Figure 2A is a subset of Figure 5A.

## RNA endpoint and denominators

The complete published signature is `workflows/rna/signature/spp1_tam_genes.txt`: SPP1, PCSK5, SLC11A1, VCAN, SLC25A37, FLNA, UPP1, BCL6, AQP9, TIMP1, VEGFA, ADM, MARCO, FN1 and IL1RN. Its source is the explicitly enumerated list in [Li et al., 2021](https://doi.org/10.3389/fimmu.2021.694801). The frozen source and verification script accompany the workflow. Scoring is an adaptation of the published signature, not a claim to run the source paper's AddModuleScore procedure.

The primary cohorts have 48/51, 19/20 and 15/16 eligible/attempted donors for GSE234933, GSE181919 and GSE310797. HN23 and HN45 are specimens from one donor; the primary analysis retains HN23. The archived PT13 count file has an incomplete row and remains in the attempted denominator. The primary model does not gate on expression of signature genes. It adjusts for log library depth after within-specimen score construction. Association, eligibility and sensitivity definitions are specified in `workflows/rna/analysis/PLAN.md`.

Equal-patient means and random-effects Fisher means answer distinct questions. Three-cohort prediction intervals are imprecise, and the reporting policy has not been calibrated by the still-unrun formal count simulation. None of the panels establishes causal regulation, treatment response or a validated universal minimum patient count.
