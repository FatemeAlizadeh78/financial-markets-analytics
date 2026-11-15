# Methodology

## Data and chronology

The original FactSet workbook uses sheet `Price History` and a header on Excel row 16. Long labels are mapped to ticker symbols; `Composite` is excluded. Levels are sorted ascending, restricted to January 2008-May 2026, and converted to simple monthly returns. June 2026 is partial and excluded. The portable loader rejects missing/nonpositive levels, duplicate dates/months, and gaps in the monthly sequence.

The selected tickers are SPY, QQQ, IWM, VGK, EFA, EEM, EWJ, SHY, IEF, TLT, AGG, LQD, HYG, EMB, TIP, GLD, DBC, VNQ, BIL, and SHV. The 60/40 equity basket uses the first seven tickers; its bond/cash basket uses SHY, IEF, TLT, AGG, LQD, BIL, and SHV. Other credit, real asset, and inflation-linked ETFs are therefore absent from this benchmark but present in the 20-ETF benchmark and optimized portfolios.

For test month i, only the immediately preceding 60 monthly returns inform allocation. Historical sample means and covariance are annualized by 12. The same constraints are applied to optimized strategies: weights sum to one, no negative positions, no leverage, and a 20% single-ETF cap. The notebook also investigates a 40% minimum-variance weight cap and Black-Litterman tau values 0.01, 0.05, and 0.10.

## Optimization and resampling

SciPy SLSQP minimizes portfolio variance or negative Sharpe. Inherited solver defaults are intentionally preserved so the portable code can be compared with the original experiment. Failed solvers fall back to equal weights; the portable functions now warn instead of failing silently. Solver tolerance sensitivity is a research limitation: extremely small covariance objectives can make default convergence criteria material.

Michaud-style resampling estimates monthly means and covariance within each past window, draws 100 Gaussian return histories of the same length, optimizes the sample covariance of each simulated history, and averages the weights. The seed is 42. This is resampled **minimum variance**, not a complete simulated efficient frontier. The normal simulation assumption does not model fat tails or regime shifts.

## Black-Litterman views

The historical prior is equal weight. Reverse optimization uses risk aversion 2.5 and annual covariance. The posterior combines this prior with two views, with tau 0.05:

1. Relative view: the ETF with the strongest trailing 12-month compounded return outperforms the weakest. The annual view is half the absolute momentum spread, clipped to 1%-6%. Confidence is 60%, 70%, or 80% for spreads below 3%, from 3% to below 8%, and at least 8%, respectively. Omega is `(1-c)/c * view_variance`, with a floor of 1e-6.
2. Absolute view: the strongest ETF's historical annualized mean is averaged with its prior-implied return (50/50), clipped to -5%-15%. Confidence is 60%; its view variance is divided by the window length in years before applying the confidence ratio, with the same floor.

The two views are correlated in construction but use a diagonal Omega. Both annualized covariance and prior receive numerical stabilization as in the notebook. The posterior mean and covariance are passed to maximum-Sharpe optimization.

The notebook's final diagnostic accepts optional local AUM values and lets users edit absolute/relative views and confidence via ipywidgets. Current AUM is excluded from the historical model because historical AUM was unavailable.

## Evaluation limits

- Annual return is the arithmetic monthly mean multiplied by 12; volatility uses sample standard deviation and sqrt(12). Sharpe assumes a zero risk-free rate.
- The original drawdown starts its running peak at the first observed cumulative wealth value. The portable CLI also includes initial capital of one, so an immediate first-month loss is counted. This intentional correction can affect drawdown values; the original results table remains labeled and unchanged.
- Original turnover is the full L1 change in target weights. It excludes drift between rebalances and incorrectly includes an initial zero row because pandas sums an all-NaN first difference to zero. Treat its reported means as descriptive notebook output, not executable trading costs.
- Fees, bid/ask spreads, slippage, taxes, currency handling, and turnover-adjusted net returns are absent. Total Return Gross levels do not make returns net of all investor costs.
- ETF selection is retrospective; survivorship/selection effects remain possible. Rolling temporal separation prevents direct future-return use but does not eliminate research selection bias.
- Parameters and strategies were not assessed on an additional untouched validation period. The results do not establish statistical superiority or future performance.
