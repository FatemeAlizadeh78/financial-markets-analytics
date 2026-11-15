# Dynamic Multi Asset Allocation

**A rolling out-of-sample comparison of classical optimization, resampling, and Bayesian portfolio views across 20 ETFs.**

Financial Markets Analytics course project by Fatemeh Alizadeh, University of Milano-Bicocca. The research asks how estimation uncertainty and systematic investor views change allocation, realized risk, and portfolio stability.

| Universe | Estimation | Evaluation | Constraints |
|---|---|---|---|
| 20 multi-asset ETFs | Previous 60 monthly returns | Next-month returns, February 2013-May 2026 | Long-only, fully invested, 20% per ETF |

## Research design

The ETF universe covers global equities, government and corporate bonds, credit, inflation-linked bonds, gold, commodities, REITs, and cash proxies. FactSet Total Return Gross levels are converted to monthly simple returns. The January 2008-May 2026 price sample contains 221 observations; 220 monthly returns yield 160 out-of-sample test months.

Six strategies share the same evaluation dates:

- **Equal weight** across all 20 ETFs.
- **60/40 benchmark**: equal-weighted baskets of seven equity ETFs and seven bond/cash ETFs.
- **Markowitz minimum variance**, using the sample covariance matrix.
- **Michaud-style resampled minimum variance**, averaging 100 optimized allocations from Gaussian simulated 60-month histories.
- **Markowitz maximum Sharpe**, using historical sample means and covariance.
- **Black-Litterman maximum Sharpe**, combining an equal-weight neutral prior with relative and absolute views derived from trailing 12-month momentum.

Every historical allocation uses `returns.iloc[i-60:i]` and is evaluated against `returns.iloc[i]`. Latest-AUM views appear only in the notebook's end-of-sample interactive diagnostic, never in historical backtests. See [methodology](docs/methodology.md) for the precise view calibration and limitations.

## Run locally

Requires Python 3.11 or newer. From this repository directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m unittest discover -s tests -v
asset-allocation --demo --simulations 2 --output outputs/demo
```

The demo uses explicitly synthetic returns. It verifies the complete pipeline without a data account and is **not** the source of the empirical results below.

To reproduce the original experiment, supply the licensed workbook as described in [data setup](data/README.md):

```bash
asset-allocation \
  --data data/FactSet_20ETF_MultiAsset_TotalReturn_2008_2026.xlsx \
  --simulations 100 \
  --seed 42 \
  --output outputs/factset
```

Each run writes monthly returns, portfolio weights, generated Black-Litterman views, a performance summary, a wealth chart, and a JSON record of the configuration and test dates. Nonempty output directories are rejected to protect existing results.

For the complete original narrative and interactive view controls:

```bash
python -m pip install -e '.[notebooks]'
jupyter lab notebooks/dynamic_asset_allocation.ipynb
```

Start Jupyter from the repository root. The last AUM diagnostic requires the optional private `data/latest_aum.json`; all preceding research can run without it.

## Results from the submitted notebook

The values below are transcribed from original notebook cell 105, not from the synthetic demo. Arithmetic annualization is used, **not CAGR**. Sharpe uses a zero risk-free rate. Costs are not included.

| Strategy | Annual return | Annual volatility | Sharpe | Max drawdown |
|---|---:|---:|---:|---:|
| Equal weight | 6.12% | 7.77% | 0.79 | -18.26% |
| 60/40 | 7.63% | 9.29% | 0.82 | -21.74% |
| Markowitz minimum variance | 2.17% | 2.13% | 1.02 | -6.56% |
| Michaud resampled | 2.23% | 2.16% | 1.03 | -6.58% |
| Markowitz maximum Sharpe | 4.71% | 3.18% | 1.48 | -7.55% |
| Black-Litterman | 6.42% | 6.19% | 1.04 | -7.43% |

The comparison shows a risk-return trade-off rather than universal dominance. Minimum-variance allocations concentrate in defensive assets; resampling changes their weights only modestly. The Black-Litterman strategy has higher turnover: the original notebook reports mean L1 target-weight changes of 0.3054, compared with 0.0400 for Markowitz minimum variance and 0.0237 for Michaud. These are neither one-way trading fractions nor drift-adjusted transaction-cost estimates.

[Machine-readable original summary](results/original_notebook_summary.csv) · [Validation record](docs/validation.md) · [Provenance and changes](docs/provenance.md)

## Repository map

```text
src/asset_allocation/    Portable methods and reproducible CLI
notebooks/              Clean, locally runnable research notebook
tests/                  Feasibility, causality, posterior, drawdown checks
results/                Attributed aggregate original results
outputs/                Generated run artifacts (ignored)
data/                   Licensed local inputs (ignored)
docs/                   Methodology, provenance, validation
.github/workflows/      Synthetic CI smoke experiment
```

The original course assignment and licensed spreadsheet remain private local source material. This repository publishes the research implementation, attributed aggregate results, and reproducibility documentation.
