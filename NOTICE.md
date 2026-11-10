# Sources and licensing

The figure and workflow code was written for PASE by the authors. The plotting adapters in this repository change paths, font selection and rendering for portability; saved data values are unchanged. The RNA analysis sources, local analysis lock, gene list and original verification record are preserved byte-for-byte. A preserved local lock identifies an earlier analysis decision; it is not a public preregistration certificate.

`workflows/rna/analysis/vendor/external_core.py` retains its accompanying `LICENSE.original-cohort` notice, including the historic spelling in that notice. The current author's correct name is **Linrui Cai**. The frozen source notice is retained as a historical license record and is not the current author list.

`workflows/rna/signature/source/Li_2021_publisher.xml` is the unmodified publisher XML of Li X, Zhang Q, Chen G and Luo D. *Multi-omics analysis showed the clinical value of gene signatures of C1QC+ and SPP1+ TAMs in cervical cancer*. Frontiers in Immunology. 2021;12:694801. [DOI](https://doi.org/10.3389/fimmu.2021.694801). Copyright 2021 Li, Zhang, Chen and Luo; distributed under CC BY 4.0. The retained 15-gene list is an attributed extraction from that article. The article attributes the underlying signature to [Zhang et al., Cell 2020](https://doi.org/10.1016/j.cell.2020.03.048).

Expression matrices are obtained separately from the original GEO accessions. This repository contains only author-generated aggregate results and source documentation, not raw cell matrices or barcode caches. Original study citations and usage conditions remain applicable.

DejaVu Sans is loaded from the installed Matplotlib package, under its bundled font license. PDFium and other third-party libraries are installed as dependencies and retain their own licenses; their binaries are not redistributed in this repository.

The current figure sources use installed Arial where available, with documented
Liberation Sans or DejaVu Sans fallbacks. No proprietary font files or Origin
application binaries are redistributed. Saved author-created Origin PDF panels
retain their embedded fonts. `current_figures/LICENSE_SCOPE.md` describes the
code, derived-table and panel-artwork licence scope. PyMuPDF and the other
installed rendering dependencies retain their own licences.
