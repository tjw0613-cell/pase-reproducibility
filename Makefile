PYTHON ?= python
.PHONY: fig1 fig2 fig3 fig4 fig5 fig6 figs1 figs2 all all-ready verify status

fig1 fig2 fig3 fig4 fig5 fig6 figs1 figs2 all all-ready verify status:
	$(PYTHON) -B reproduce.py $@
