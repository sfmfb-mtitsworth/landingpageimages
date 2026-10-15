"""Extract national CPI-U from the BLS Public Data API and write data/cpi_national.json.

Series:
  CUUR0000SA0    All items, U.S. city average, not seasonally adjusted (used for YoY)
  CUSR0000SA0    All items, seasonally adjusted (used for MoM)
  CUUR0000SA0L1E All items less food and energy (core), NSA (used for core YoY)

Set BLS_API_KEY to use the v2 API with a registration key (higher limits). Without
it, the v2 API still works for up to 10 years and 25 requests per day.
"""

import datetime as dt
import json
import os
import pathlib
import sys
import urllib.request

API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
SERIES = {
    "CUUR0000SA0": "headline_nsa",
    "CUSR0000SA0": "headline_sa",
    "CUUR0000SA0L1E": "core_nsa",
}
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "cpi_national.json"


def extract(start_year, end_year):
    body = {"seriesid": list(SERIES), "startyear": str(start_year), "endyear": str(end_year)}
    key = os.environ.get("BLS_API_KEY")
    if key:
        body["registrationkey"] = key
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.load(resp)
    if payload.get("status") != "REQUEST_SUCCEEDED":
        raise RuntimeError(f"BLS request failed: {payload.get('message')}")
    return payload


def transform(payload):
    """Merge the series into one row per month with derived YoY and MoM changes."""
    by_month = {}
    for series in payload["Results"]["series"]:
        field = SERIES[series["seriesID"]]
        for obs in series["data"]:
            if not obs["period"].startswith("M") or obs["period"] == "M13":
                continue
            try:
                value = float(obs["value"])
            except ValueError:  # "-" marks a missing observation
                continue
            month = f"{obs['year']}-{obs['period'][1:]}"
            by_month.setdefault(month, {"month": month})[field] = value

    rows = [by_month[m] for m in sorted(by_month)]
    index = {r["month"]: r for r in rows}
    for r in rows:
        y, m = map(int, r["month"].split("-"))
        prior_year = index.get(f"{y - 1}-{m:02d}")
        prev = index.get(f"{y - (m == 1)}-{(m - 2) % 12 + 1:02d}")
        r["yoy"] = _pct(r.get("headline_nsa"), prior_year and prior_year.get("headline_nsa"))
        r["core_yoy"] = _pct(r.get("core_nsa"), prior_year and prior_year.get("core_nsa"))
        r["mom"] = _pct(r.get("headline_sa"), prev and prev.get("headline_sa"))
    return rows


def _pct(cur, base):
    if cur is None or not base:
        return None
    return round((cur / base - 1) * 100, 2)


def main():
    today = dt.date.today()
    payload = extract(today.year - 9, today.year)
    rows = transform(payload)
    if not rows:
        sys.exit("BLS returned no observations")
    out = {
        "source": "U.S. Bureau of Labor Statistics, CPI-U, U.S. city average",
        "series": SERIES,
        "fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "latest_month": rows[-1]["month"],
        "rows": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(f"Wrote {len(rows)} months through {out['latest_month']} to {OUT}")


if __name__ == "__main__":
    main()
