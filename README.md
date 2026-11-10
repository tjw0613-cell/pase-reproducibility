# PASE manuscript reproduction

Rebuild the figures for the **9 November 2026 revised manuscript**, or follow
the archived workflows to recompute its core analyses. For the general
`pase.associate()` API, use the separate
[software repository](https://github.com/tjw0613-cell/pase-software).

## Choose a task

| Task | Start here |
|---|---|
| Rebuild Figures 1–6 and S1–S2 | The commands below; all required figure inputs are included. |
| Inspect each panel's source and construction | [FIGURES.md](FIGURES.md) and [current_figures](current_figures/). |
| Recompute the completed 293-condition simulation or balanced count benchmark | [ARCHIVES.md](ARCHIVES.md), using results DOI [24015713](https://doi.org/10.5281/zenodo.24015713). |
| Read the protocol archived before the formal simulation | Protocol DOI [24010816](https://doi.org/10.5281/zenodo.24010816). |
| Rerun the primary RNA analysis from GEO counts | [RNA download and analysis guide](workflows/rna/README.md). |
| Rerun the later detection-matched controls or unequal-yield memento extension | Supplementary Data S1 and S2 supplied with the manuscript; see [ARCHIVES.md](ARCHIVES.md). These are not included in DOI 24015713. |

The previous repository revision was prepared before the formal simulation.
Its `fig3` and `fig4` targets stopped without drawing a figure. The current
targets use completed results. Earlier repository history remains available
in Git; earlier drawings must not be used as the current manuscript figures.

## Install

Clone this repository and use Python 3.11 or later. These commands use the new
environment's Python directly, so environment activation is unnecessary.

**Windows PowerShell**

```powershell
git clone https://github.com/tjw0613-cell/pase-reproducibility.git
cd pase-reproducibility
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe reproduce.py verify
.\.venv\Scripts\python.exe reproduce.py all
```

**macOS / Linux**

```bash
git clone https://github.com/tjw0613-cell/pase-reproducibility.git
cd pase-reproducibility
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python reproduce.py verify
.venv/bin/python reproduce.py all
```

With that environment activated, `python reproduce.py fig3` rebuilds one
figure; `python reproduce.py figs2` builds Supplementary Figure S2. Use
`--output-dir "my figures"` to select another output directory. `make fig3`
is an optional equivalent. `all-ready` remains an alias for `all`.

## What the figure commands do

Figures 2–6 and S1 are **vector compositions of saved Origin data panels**.
Their inputs and source tables are included. Figure 1 is redrawn from its
fixed schematic coordinates, and Figure S2 is plotted from its saved unequal-yield benchmark
table. The commands produce PDF, PNG and TIFF files plus an output record.
They do not refit models, rerun the simulation or launch Origin. Editing
panel data in Origin requires the separate editable artwork supplied to the
authors. See [FIGURES.md](FIGURES.md) for the distinction between panel
recomposition, plotting saved estimates and recomputing analyses.

All distributed inputs are checked against SHA-256 manifests before use.
`python scripts/check_delivery.py` checks a relocated copy, including Figures
3/4, all eight PDF outputs and input-tampering protection. GitHub Actions runs
the checks on Linux, macOS and Windows; the status of each actual run is shown
in [Actions](https://github.com/tjw0613-cell/pase-reproducibility/actions).
An intact input package or a passing figure check does not by itself verify a
fresh raw-data analysis.

## Versions and citation

See [VERSION_MAP.md](VERSION_MAP.md) for the manuscript, software, protocol,
result archive and later supplementary analyses. The old DOI
[23032874](https://doi.org/10.5281/zenodo.23032874) is a historical archive;
it is not the current core-results entry point. Cite the version-specific DOI
for the materials actually used, and the commit or release of this figure
repository when reproducing its artwork.

Source code is MIT licensed. Author-generated documentation and derived
tables are CC BY 4.0. Third-party source materials retain their original
notices; see [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md). External GEO count
matrices are downloaded separately and are not redistributed here.
