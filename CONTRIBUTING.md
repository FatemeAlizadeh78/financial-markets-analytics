# Reproducing and extending the experiment

Keep the attributed original results separate from new experiments. Use a new output folder for every configuration and preserve the generated `run.json`. Report sample dates, estimation window, random seed, solver behavior, turnover definition, risk-free assumption, and costs with any performance claim.

Before a change, run the unit tests and synthetic smoke experiment from the README. Changes to temporal splits, Black-Litterman view calibration, optimization tolerances, or constraints need an explicit methodology update. Never commit provider workbooks, private AUM inputs, credentials, or executed notebook outputs.

Promising research extensions include transaction-cost-aware rebalancing, covariance shrinkage, non-Gaussian resampling, and evaluation on a separately held-out period. These are proposed extensions rather than implemented features.
