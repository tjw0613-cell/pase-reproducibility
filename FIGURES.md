# Current figure and source map

The figure inputs correspond to the revised manuscript of **9 November 2026**.
`current_figures/FIGURE_MANIFEST.json` lists dimensions and construction modes;
the input manifest verifies the actual panel, table and drawing files.
`current_figures/SOURCE_ORIGINS.json` records their source locations. Those
historical location labels are not runtime dependencies.

| Target | Current content | Construction |
|---|---|---|
| `fig1` | Patient-level workflow; equal, random-effects and individual shrinkage summaries | Schematic artwork; positions are illustrative, not fitted biological data. |
| `fig2` | Gaussian null rejection, patient duplication, individual patient cell counts | Compose saved Origin panels. Eight patients and 2,000 cohorts per Gaussian allocation; RNA counts include unavailable records explicitly. |
| `fig3` | Count-data coverage and signed-control rejection across patient counts and heterogeneity | Compose saved Origin heatmaps from the completed formal experiment; six interval methods, distinct arithmetic and Fisher targets. |
| `fig4` | Cell-yield coupling, bias/error/width, and gated-minus-ungated changes | Compose the nine saved Origin panels. No removed availability-only row is reintroduced. |
| `fig5` | Gaussian rejection, 999 within-patient shuffles, runtime, balanced native count benchmark | Compose saved Origin panels. The native benchmark uses **500 cohorts per scenario**, not the historical 100-attempt pilot. Memento shuffles were not run. |
| `fig6` | Individual patient correlations and cohort summaries; 10/30/50-cell sensitivity; paired gating shifts | Compose saved Origin panels. There is no old reporting-flow panel D. |
| `figs1` | Detection-matched gene comparisons and LILRB4's position | Compose saved Origin panels from the later A1 analysis. |
| `figs2` | Unequal-yield native memento comparison | Plot saved summary values from the later 1,500-cohort extension. |

Complete captions are in [captions](captions/). The individual source tables,
panel plans and numerical values are provided in
[current_figures](current_figures/). Counts, covariance adjustments, targets
and limits should be read with those captions; the figure commands do not
re-estimate them.

## Three distinct reproduction tasks

1. **Compose the current artwork:** `python reproduce.py all`. Origin-exported
   vector panels are placed into the final layout; the Origin application is
   not required. This does not recalculate the panel from observations.
2. **Inspect or replot saved data:** use the supplied source tables and panel
   plans. The author-editable Origin projects are supplied separately; this
   repository does not pretend that PDF composition is an editable Origin fit.
3. **Recompute analyses:** follow [ARCHIVES.md](ARCHIVES.md) and the
   [RNA workflow](workflows/rna/README.md). Full S1/S2 workflows are supplied
   as manuscript supplements, separately from core DOI 24015713.

The historical tables in `data/count_pilot` and old records under `historical`
are retained for traceability. Current figure commands do not read the pilot
tables. Older figure scripts remain available through Git history.

## Interpretation

Equal-patient means and Fisher-scale random-effects means have different
targets. Patient-wise sign controls are zero-population-mean experiments, not
individual-patient sharp nulls. Cell selection can change the fitted
population and scores; the RNA and simulation gating shifts do not prove a
causal biological mechanism. The software's patient-count reporting defaults
are result-informed choices rather than validated adequacy thresholds.

The 15-gene RNA list and its source attribution remain in
[the signature workflow](workflows/rna/signature/). Raw GEO expression
matrices are not included. No statistical results are changed by the present
documentation and figure-entry repair.
