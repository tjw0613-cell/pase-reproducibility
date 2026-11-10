# Current manuscript figures

This directory regenerates Figures 1–6 and S1–S2 from the checked plotting sources used in the revised manuscript. The command does not rerun the statistical analyses.

```bash
python -m pip install -r current_figures/requirements.txt
python current_figures/render.py --verify-only
python current_figures/render.py --figure fig3 --output-dir outputs
python current_figures/render.py --figure all --output-dir outputs
```

The default selection is `all`; the eight names are `fig1`, `fig2`, `fig3`, `fig4`, `fig5`, `fig6`, `figs1` and `figs2`. Paths are relative to the script, so the repository can be moved. An output directory can be anywhere outside this source directory. Existing outputs with the same figure names are replaced; source files are never modified.

| Figures | What the command regenerates | Input and boundary |
| --- | --- | --- |
| 1 | A vector schematic from the fixed cell and summary coordinates | Two illustrative CSVs in `schematic/`; these are not empirical measurements. |
| 2–6, S1 | The full vector layout, including panel placement, labels, legends and colour bars | 33 frozen Origin PDF data panels in `panels/`; each is bound to its plan and source table. Data marks remain the original Origin exports. This is composition, not a new Origin fit or a raw-count rerun. |
| S2 | A data plot from the final rejection-rate and Wilson-interval table | `inputs/native_allocation_comparison.tsv` has 18 rows: two allocations × three scenarios × three methods; 500 attempted cohorts per scenario and allocation. |

Every figure is 180 mm wide. Heights are recorded individually in `FIGURE_MANIFEST.json`. Outputs are vector PDF and SVG, PNG at 300 dpi (S2: 600 dpi), and 600 dpi TIFF. Receipt JSON files record the input manifest, selected fonts, dimensions and output hashes. They do not certify visual review or analysis reproduction.

Arial matches the submitted figures. No proprietary font files are distributed. If Arial is not installed, the renderer uses installed Liberation Sans or DejaVu Sans and records a warning; text metrics and pixels may differ. The Origin panels retain their original embedded fonts. Install Arial where licensed to obtain the closest presentation match.

`FILES.sha256.json` checks the packaged files. `SOURCE_ORIGINS.json` records original hashes and adaptations; its historic source labels are not executable paths. `plans/` records the exact panel data and drawing specifications. Do not silently replace a source table while retaining an old panel: regenerate the Origin panel, update its plan and manifests, and inspect the resulting figure together.

The historical public results release is [Zenodo 10.5281/zenodo.24015713](https://doi.org/10.5281/zenodo.24015713). Later exploratory detection-matched analyses are supplied as Supplementary Data S1. The additional 1,500 unequal-cell memento cohorts and Figure S2 sources are supplied as Supplementary Data S2. Those later supplements are not claimed to be contained in that older DOI. The current Fig 5D uses the completed balanced benchmark with 500 attempted cohorts per scenario, not the earlier 100-cohort pilot.

The complete editable Origin projects are delivered separately with the manuscript artwork. They are not required for this portable composition route. Raw-data workflows and their distinct verification scopes are described at the repository root.

Code is MIT-licensed; author-created documentation, plotted aggregate results and panel artwork are CC BY 4.0. See `LICENSE_SCOPE.md` and the repository licence. Original third-party data are not redistributed here.
