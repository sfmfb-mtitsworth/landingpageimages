# ETL

Daily scripts that pull public data and render artifact pages.

| Script | Source | Output |
|---|---|---|
| `cpi_national.py` | BLS CPI-U, U.S. city average (headline NSA + SA, core NSA) | `data/cpi_national.json` |

`render.py <name>` injects `data/<name>.json` into `etl/templates/<name>.html` and writes `artifacts/<name>.html`, the page that gets published as the artifact.

A daily Claude Code Routine runs both, commits changes and republishes the artifact at https://claude.ai/artifact/1kc7BQ15sx9YVH6EJg5kM5. `.github/workflows/etl-daily.yml` is a manual fallback. Add a `BLS_API_KEY` repo secret (free at https://data.bls.gov/registrationEngine/) for higher API limits.

Adding a new feed: write `etl/<name>.py` that writes `data/<name>.json`, add a template, and add a job to the workflow.
