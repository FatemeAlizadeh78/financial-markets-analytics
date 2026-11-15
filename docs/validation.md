# Validation record

Validated locally on 2026-11-15 using an isolated Python 3.13 environment, installed from `pyproject.toml`. Exact resolved versions are recorded in `requirements-lock.txt`; the declared version ranges support Python 3.11 and newer. GitHub Actions is configured for Python 3.11 but has not been run remotely.

## Checks completed

- All four unit tests passed: optimizer feasibility; stability of earlier allocations when future returns change; finite/symmetric Black-Litterman posterior; and drawdown against initial capital. The temporal-invariance assertion allows 1e-6 numerical optimization tolerance.
- Every code cell in the cleaned notebook was parsed successfully, including correction of a prose cell that was originally stored as code.
- Notebook execution counts, stored outputs, and provider-specific hidden metadata were removed.
- The synthetic CLI demo completed with two Michaud simulations per window. It produced structured outputs and a chart without any external data or network call.
- The **full empirical CLI experiment completed** against the supplied local workbook using 100 Michaud simulations per window, seed 42, all six strategies, and 160 test months. The resulting summary agrees with the original stored notebook table to two decimal places.
- The generated empirical wealth chart was visually inspected.
- Local raw workbooks, environment files, generated outputs, and archives are ignored by Git. The candidate publication files were scanned for personal contact details, academic identifiers, and credentials; none were retained. The author's name remains as attribution.

## Empirical reproduction

The new CLI produced the following rounded values:

| Strategy | Arithmetic annual return % | Annual volatility % | Zero-rf Sharpe | Max drawdown % |
|---|---:|---:|---:|---:|
| Equal weight | 6.12 | 7.77 | 0.79 | -18.26 |
| 60/40 | 7.63 | 9.29 | 0.82 | -21.74 |
| Markowitz minimum variance | 2.17 | 2.13 | 1.02 | -6.56 |
| Michaud resampled | 2.23 | 2.16 | 1.03 | -6.58 |
| Markowitz maximum Sharpe | 4.71 | 3.18 | 1.48 | -7.55 |
| Black-Litterman | 6.42 | 6.19 | 1.04 | -7.43 |

The methodology documents limitations and the CLI's corrected initial drawdown baseline. Passing checks demonstrates reproducibility and temporal input separation, not statistical significance or a profitable net trading strategy.

## Not performed

The entire interactive notebook, including the optional private-AUM widget, was not re-executed end to end in a fresh Jupyter frontend. Its analytical functions and all six main historical strategies were exercised through the CLI. A local notebook launch requires the optional notebook dependency group and licensed inputs. No remote CI run, push, deployment, or public hosting was performed.
