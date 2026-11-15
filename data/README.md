# Local input data

The complete source workbook is available locally in this directory but ignored by Git. A fresh clone needs its own authorized copy; the repository does not redistribute licensed FactSet observations.

Expected file: `FactSet_20ETF_MultiAsset_TotalReturn_2008_2026.xlsx`.

Expected format: Excel sheet `Price History`, header at row 16, a `Date` column, and 20 total-return level columns whose labels end in `(TICKER-US)`. See `src/asset_allocation/cli.py` for the exact ticker list. A cleaned date range of January 2008-May 2026 is used; do not silently substitute closing prices for Total Return Gross levels.

For the optional final notebook AUM diagnostic, create an ignored `latest_aum.json` mapping every ticker to a same-date AUM string, such as `"SPY": "753B"`. Supply all 20 tickers, document your retrieval date locally, and use the data only for the end-of-sample analysis. This file is not needed for CLI runs or historical notebook backtests.

Use `asset-allocation --demo` to run without licensed data. Synthetic output must not be described as the original course result.
