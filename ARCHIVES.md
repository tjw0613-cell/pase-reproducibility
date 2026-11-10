# Software, analysis archives and manuscript supplements

Use the entry that matches the task. Rebuilding a figure from saved results is
separate from generating new simulated cohorts or fitting the raw RNA data.

| Task | Material | Version and scope |
|---|---|---|
| Use `pase.associate()` | [PASE software](https://github.com/tjw0613-cell/pase-software), [PyPI 1.1.0](https://pypi.org/project/pase-framework/1.1.0/) | Software 1.1.0 is the version used in the archived study. Later documentation releases do not change that version identity. |
| Inspect the simulation plan | [Protocol DOI 10.5281/zenodo.24010816](https://doi.org/10.5281/zenodo.24010816) | Protocol 2.0.0, publicly archived before the formal count simulations. This is a protocol, not the completed results. |
| Recompute reports from stored formal simulations | [Results DOI 10.5281/zenodo.24015713](https://doi.org/10.5281/zenodo.24015713) | Five ZIPs listed below; 293 conditions and 3,302,000 cohorts. Includes the balanced native benchmark and 15-gene RNA analyses. |
| Rebuild current manuscript artwork | [Current figure guide](FIGURES.md) | Current repository targets use the revised figure sources. The 6 November archive preserves earlier layouts. |
| Refit the public RNA cohorts | [RNA instructions](workflows/rna/README.md) | GEO downloads, extraction, fitting and verification. Raw GEO matrices are obtained separately. |
| Reproduce the later gene controls | `Supplementary_Data_S1.zip`, submitted with the manuscript | Detection-matched gene controls; not included in results DOI 24015713. |
| Reproduce the later unequal-yield native benchmark | `Supplementary_Data_S2.zip`, submitted with the manuscript | Three scenarios of 500 cohorts each; not included in results DOI 24015713 or the 293-condition formal count study. |

The earlier [archive 23032874](https://doi.org/10.5281/zenodo.23032874) is a
historical resource. It is not the software 1.1.0 or revised formal-results
archive. The subsequent results record and the original protocol have distinct
version DOIs, even though Zenodo places them in one version series. Cite each
specific DOI for its own contents.

## Obtain and verify the published results

The exact filenames, sizes, SHA-256 values and download URLs are recorded in
[archives.json](archives.json), transcribed from the deposited
`SHA256SUMS.txt` and `README_RELEASE.md`.

| Selection | ZIP filename | Download size | Contents |
|---|---|---:|---|
| `count-code` | `pase-count-code-and-figures-2026-11-06.zip` | 17.3 MB | Frozen protocol, reporting code and earlier figure sources |
| `count-results` | `pase-count-results-2026-11-06.zip` | 2.94 GB | Stored study/reference effects, intervals, summaries and seeds |
| `software` | `pase-framework-1.1.0.zip` | 197 KB | Published wheel/source distribution and checks |
| `native` | `pase-native-benchmarks-2026-11-06.zip` | 24.0 MB | Balanced benchmark: 3 scenarios × 500 cohorts; scCOSMiX feasibility |
| `rna` | `pase-rna-15gene-2026-11-06.zip` | 1.52 MB | RNA code and results; no raw GEO matrices |

From this repository root, inspect the list or download only the package you
need. The download helper uses the Python standard library and checks both size
and SHA-256. It does not extract files or replace an existing conflicting file.

```text
python scripts/fetch_archive.py --list
python scripts/fetch_archive.py count-code --dest downloads
```

To obtain the large results package, request it explicitly:

```text
python scripts/fetch_archive.py count-results --dest downloads
```

If you downloaded a ZIP in your browser, put it in `downloads/` with its exact
filename and verify it without a network request:

```text
python scripts/fetch_archive.py count-code --dest downloads --verify-only
python scripts/fetch_archive.py count-results --dest downloads --verify-only
```

The helper never downloads all packages automatically. If Zenodo is unavailable,
retain the existing files and retry later; do not change the expected hashes.

## Recreate the archived count reports

Extract **both** count ZIPs into one new directory, for example `archive-count/`.
Use your archive application to combine them without replacing existing,
different files. The resulting layout must include these sibling directories:

```text
archive-count/
  protocol/
  run/
  analysis/
  reporting/
```

Use the Python environment specified in `protocol/environment.json` and
`protocol/requirements-lock.txt`; the plotting layer additionally uses
Matplotlib and Pillow as recorded in the archive. Change into `archive-count/`
and run the documented commands:

```text
python -B protocol/runner/run.py status --plan protocol/design/design.json --grid protocol/design/grid.csv --out run
python -B protocol/report/threshold_report.py --grid protocol/design/grid.csv --run run --out regenerated_threshold_tables
python -B analysis/audit_simulation_decision.py final --protocol protocol --run run --out regenerated_decision
python -B reporting/render_final_figures.py --protocol protocol --run run --out regenerated_figures
```

These commands read stored results and rebuild the **6 November 2026 reports
and figure layouts**. Use this repository's current figure targets for the
later manuscript artwork. Recreating these reports does not refit the millions
of simulated datasets. A fresh formal run requires the archived runner
instructions, original protocol verification, compatible dependencies and CUDA;
see `protocol/runner/RUNNER.md`. Use a fresh output location and keep the stored
`run/` and frozen protocol unchanged.

The archive stores patient-effect and interval arrays, rather than every
simulated cell-level count matrix. The generator and seed streams reconstruct
those cell-level observations. Identical floating-point bytes across hardware
are not promised.

## RNA and native-method analyses

Extract `rna`, `native` and `software` into **separate** directories so their
README and licence files cannot overwrite one another. Follow each package's
own README and environment requirements. For exact raw GEO filenames,
download links, safe extraction and analysis commands, use the
[RNA guide](workflows/rna/README.md).

The archived balanced native comparison contains 1,500 attempted cohorts. Its
100-cohort pilot is included in those 500-per-scenario results, not an extra
experiment. The later unequal-yield benchmark adds 1,500 cohorts in S2; those
are distinct from both the balanced benchmark and the formal 293 conditions.

## Later manuscript supplements

S1 and S2 are supplied to the journal with the manuscript. No public download
URL for them is asserted here. Their expected identities for the current
submission copy are:

| File | Bytes | SHA-256 |
|---|---:|---|
| `Supplementary_Data_S1.zip` | 2,915,498 | `e9a15ff815279ac9a9fea94d06b5427a096249901b0b46a53ce6f63cd0c234e0` |
| `Supplementary_Data_S2.zip` | 67,128,828 | `dda7786a3b40d753e1a23f816323fa841f798ba203025b54e8000d4cd98a8dee` |

Once you have those files, extract each into a separate directory and follow
its own README. Their code, complete results and verification records are not
retroactively part of DOI 24015713. Original code is MIT licensed; original
documentation and aggregate results are CC BY 4.0. Source data and third-party
code retain their original notices and terms.
