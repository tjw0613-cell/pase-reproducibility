# Completed formal count simulation

The formal negative-binomial experiment completed **293 generating conditions
and 3,302,000 simulated cohorts**. Its protocol was publicly archived as
[version 2.0.0, DOI 24010816](https://doi.org/10.5281/zenodo.24010816) before
the formal study and reference draws. The completed code, saved results and
reporting layer are in [results DOI 24015713](https://doi.org/10.5281/zenodo.24015713).

Use `python reproduce.py fig3` or `fig4` to compose the current manuscript
figures from saved Origin panels. This is not a new statistical run. To
recompute result summaries or regenerate the archived simulation figures,
follow [ARCHIVES.md](ARCHIVES.md). To generate new simulation observations,
follow the frozen protocol's runner instructions and use a fresh output
directory. Do not overwrite the archived run or edit the frozen protocol.

The primary workflow uses a 15-gene score and depth-only adjustment.
Arithmetic patient-correlation means and Fisher-scale summaries have
separate targets. The patient-count reporting defaults were selected after
the results were examined; the protocol DOI does not make those later
choices prospectively registered.

The old severe-patient-loss experiment and the new within-patient gene-loss
stress use different missingness mechanisms. Higher interval availability
in the new design is not evidence that a method corrected the old severe
loss. The historical Gaussian controls, balanced native benchmark and later
unequal-yield extension are separate evaluations, not additional conditions
of the 293-condition experiment.

The earlier repository revision described Fig 3/4 as unavailable. That text
and its refusal to draw those figures remain in Git history; they do not
describe the completed materials linked above.
