# Source provenance and adaptation

Reviewed source archive: `FMA_Alizadeh.zip`, supplied by the user on 2026-11-15. It contains exactly three assets:

| Asset | Review and treatment |
|---|---|
| `Financial_Markets_Analytics.ipynb` | All 129 cells reviewed, including narrative, code, and stored numerical output. Preserved as a locally portable notebook with all outputs/execution state stripped. |
| `Homework FMA 2026 - Variant B - Dynamic Asset Allocation .pdf` | Three assignment pages read and visually inspected. Describes Markowitz, Michaud, optional Black-Litterman, multi-asset data, and out-of-sample evaluation. Kept outside this repository. |
| `FactSet_20ETF_MultiAsset_TotalReturn_2008_2026.xlsx` | Workbook sheet and complete selected monthly series inspected through the loader. Licensed local copy ignored by Git; not published. |

The original files and their SHA-256 inventory remain in the parent workspace's private `sources/project-review/financial/` directory. The public-facing repository is self-contained for the synthetic demo; access to the original workbook is necessary for empirical reproduction.

## Changes made for portability

- Removed Google Colab Drive mounting and replaced the absolute Drive path with a local path or the `FMA_DATA_PATH` environment variable.
- Cleared all notebook output and notebook metadata. Moved the original hard-coded latest-AUM dictionary to an optional ignored JSON input.
- Corrected original cell 104 from a prose-containing code cell into Markdown. The original cell numbering is retained throughout the notebook.
- Extracted optimizer, resampling, view-generation, posterior, and manual-view matrix functions into an importable module. Failed optimization now emits a warning before the inherited equal-weight fallback.
- Added a command-line rolling experiment with validated input chronology, structured run artifacts, configuration metadata, and a clearly identified synthetic demo.
- Corrected the CLI's drawdown baseline to include initial capital. No corrections were applied retrospectively to the attributed original result CSV.
- Retained the full interactive AUM/manual-view notebook extension; the CLI focuses on the six historical strategies. Notebook-only cap/tau sensitivity experiments remain available in the notebook.

No additional statistical result or author contribution has been invented. This packaging distinguishes newly added reproducibility infrastructure from the original academic experiment. The university assignment and vendor dataset are not offered under a new license; no blanket license was applied without an author decision.
