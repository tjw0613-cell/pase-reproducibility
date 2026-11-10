# Which version should I use?

| Material | Version / location | Scope |
|---|---|---|
| Manuscript and current figures | Revised manuscript, 9 November 2026; this repository's current figure inputs | Six main figures and two supplementary figures. This repository does not publish the manuscript text. |
| Software used for the reported analyses | [PASE 1.1.0](https://pypi.org/project/pase-framework/1.1.0/) | `pase.associate()` and the reporting policy. Later documentation-only patches do not retroactively change the analysis version. |
| Formal simulation protocol | [10.5281/zenodo.24010816](https://doi.org/10.5281/zenodo.24010816), protocol 2.0.0 | Frozen design and executable protocol, archived before the new formal simulations. |
| Core code and results | [10.5281/zenodo.24015713](https://doi.org/10.5281/zenodo.24015713), deposited 6 November 2026 | Software, 293-condition count experiment, balanced native benchmark with 500 cohorts per scenario, and primary RNA workflows. The archived figure style predates the current artwork. |
| Detection-matched gene controls | Supplementary Data S1 accompanying the manuscript | Later A1 analysis; not in core DOI 24015713. Its saved Figure S1 source data are included for figure reconstruction here. |
| Unequal-yield native count benchmark | Supplementary Data S2 accompanying the manuscript | Later 1,500-cohort extension (three scenarios × 500), not in core DOI 24015713. Figure S2 is plotted from its saved summary here. |
| Earlier analysis archive | [10.5281/zenodo.23032874](https://doi.org/10.5281/zenodo.23032874) | Historical materials; do not use this as the current results archive. |

The protocol and core results happen to belong to the same Zenodo version
series. Cite their specific version DOIs separately: the concept DOI or its
latest-version redirect cannot identify both the protocol and its later
results unambiguously.

The complete later S1/S2 archives are supplied with the manuscript; this
repository includes only the tables/artwork required for the figures. It does
not claim those later analyses were part of the frozen formal simulation or
the earlier public archive.

## Updating documentation

README and link repairs can be published through a repository commit or a
documentation-only software patch. They do not require altering the
published protocol or result files. Any future change to archived analysis
content should receive its own clearly described version.
