# PASE manuscript reproduction

Reconstruct PASE manuscript figures from their saved results, or run the separate RNA-cohort workflow from public count files.

## Install

Use Python 3.11 or later in a virtual environment:

```text
python -m venv .venv
python -m pip install -r requirements.txt
```

Activate `.venv` before the second command (`.venv\Scripts\Activate.ps1` in Windows PowerShell, or `source .venv/bin/activate` on Linux/macOS). All commands below work without GNU Make. The code uses DejaVu Sans distributed with Matplotlib and the PDFium renderer distributed with pypdfium2; no system font or external PDF executable is required.

The exact installed versions used for the local Windows/Python 3.13 check, including the optional RNA dependencies, are recorded in `requirements-lock-windows-py313.txt`. This records the tested environment; Linux/macOS compatibility is not inferred from the Windows check.

The supplied GitHub Actions workflow schedules figure checks on Linux, macOS and Windows with Python 3.11/3.13. It has not run on GitHub as part of this local preparation. To repeat the local package check after rendering, install the optional RNA requirements and run `python scripts/check_delivery.py`; it verifies checksums, moves a copy into a temporary directory with spaces in its name, reconstructs the ready figures and tests the unavailable targets.

## Five-line example

```text
python reproduce.py verify
python reproduce.py fig1
python reproduce.py fig2
python reproduce.py fig5
python reproduce.py fig6
```

`python reproduce.py all-ready` runs those four figures. `make fig2` and `make all-ready` are optional equivalents. Each figure also has its own entry point, for example `python scripts/fig2.py`. An explicit output location is supported: `python reproduce.py fig6 --output-dir figures`.

## What is ready

| Figure | Content | Current status |
|---|---|---|
| 1 | Patient-level framework and distinct aggregation targets | Reconstructed from diagram instructions |
| 2 | Clustered Gaussian controls and donor-duplication sensitivity | Reconstructed from verified saved results |
| 3 | Unified count-data calibration across patient counts and heterogeneity | Formal results not available |
| 4 | Informative cell yield, weighting and detection-gate effects | Formal results not available |
| 5 | Completed method comparisons, real-data controls and resource measurements | Reconstructed from verified saved results |
| 6 | Three-cohort biological application and reporting workflow | Reconstructed from verified saved results |

`python reproduce.py fig3` and `fig4` stop with exit code **2** and create no image. The unified negative-binomial protocol has not been publicly archived and the formal simulation has not been run. [FORMAL_SIMULATION.md](FORMAL_SIMULATION.md) states what must exist before these targets can be implemented. The completed Gaussian controls and small count-input pilot are separate experiments.

## Inputs and outputs

Small author-generated result tables are in `data/`. Every input has a size and SHA-256 in [source_manifest.json](source_manifest.json); each figure checks that manifest before reading data. [FIGURES.md](FIGURES.md) maps every panel to its exact table and statistical meaning. Rendering does not fit statistical models or create new observations.

Each ready figure produces a vector PDF, a 300-dpi PNG, a 600-dpi LZW-compressed TIFF and an output manifest in `outputs/`. Figure 6 additionally produces SVG. The fixed width is 6.5 inches; insert figures at the same physical width to keep lettering consistent. File hashes can differ with library versions, so the saved data and their interpreted numbers are the scientific comparison, rather than a promise of identical raster bytes on every computer.

## Start from raw RNA counts

[workflows/rna/README.md](workflows/rna/README.md) gives exact source filenames, download links, extraction and analysis commands, verification and cohort pooling. Frozen scripts and their original analysis lock are included. The full count matrices and private caches are not included. The packaging checks reran the figure reconstruction and checked the frozen source hashes; they did **not** perform another end-to-end extraction and fit of all raw cohorts. The earlier independent numerical check is retained with its original status in `workflows/rna/evidence/`.

The RNA workflow targets the published **15-gene SPP1 macrophage signature**. It is not the former four-gene demonstration in the older archive. Full fresh method benchmarking, external R-package fits and new resource profiling are outside this compact figure repository.

## Software and citation

This repository is separate from the installable [PASE software](https://github.com/tjw0613-cell/pase-software), distributed as `pase-framework` and imported as `pase`. Use the software repository for the `pase.associate` API and its small tutorial. Use this repository for manuscript-specific figures and frozen cohort computations.

The earlier public PASE archive is [Zenodo v3, 10.5281/zenodo.23032874](https://doi.org/10.5281/zenodo.23032874). That DOI does **not** identify this newly prepared repository or an unrun simulation. A version-specific identifier for this package must be assigned when this package is published. Current authors: Jinwei Tang, Yunfan Lin, Linrui Cai, Yali Wen, Guangyang Chen and Li Huang.

Source code is MIT licensed; author-generated documentation and derived tables are CC BY 4.0. Third-party source materials retain their own notices; see [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
