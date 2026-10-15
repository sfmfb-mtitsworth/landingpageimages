"""Render an artifact page by injecting a data JSON file into its HTML template.

Usage: python etl/render.py cpi_national
Reads data/<name>.json and etl/templates/<name>.html, writes artifacts/<name>.html.
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PLACEHOLDER = "/*__CPI_DATA__*/null"


def render(name):
    data = json.loads((ROOT / "data" / f"{name}.json").read_text())
    template = (ROOT / "etl" / "templates" / f"{name}.html").read_text()
    if PLACEHOLDER not in template:
        sys.exit(f"Template {name}.html has no {PLACEHOLDER} placeholder")
    # Escape "</" so the JSON can't close the <script> tag early.
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    out = ROOT / "artifacts" / f"{name}.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(template.replace(PLACEHOLDER, payload))
    print(f"Rendered {out}")


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else "cpi_national")
