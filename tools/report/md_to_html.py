#!/usr/bin/env python3
"""Render a Markdown document to a self-contained HTML file.

Images referenced with relative paths are embedded as base64 data URIs, so
the HTML renders anywhere (chat preview, browser, email) with no side files.

Usage: python3 tools/report/md_to_html.py <input.md> [output.html]

Needs the `markdown` package (not a runtime dependency of the app).
"""

from __future__ import annotations

import base64
import pathlib
import re
import sys

# tools/report/html.py would shadow the stdlib `html` package that markdown
# imports, and a script always puts its own directory first on sys.path
_HERE = str(pathlib.Path(__file__).resolve().parent)
sys.path[:] = [p for p in sys.path if p not in ("", ".", _HERE)]

import markdown  # noqa: E402

CSS = """
:root { color-scheme: dark; }
body { background: #0b0c14; color: #cbd2dd; margin: 0; padding: 48px 24px 96px;
       font-family: "Geist", system-ui, -apple-system, "Segoe UI", sans-serif;
       line-height: 1.65; }
main { max-width: 980px; margin: 0 auto; }
h1 { color: #fff; font-size: 30px; line-height: 1.25; margin: 0 0 8px; }
h2 { color: #fff; font-size: 22px; margin: 44px 0 12px;
     border-bottom: 1px solid #1d2435; padding-bottom: 8px; }
h3 { color: #e6ebf3; font-size: 17px; margin: 28px 0 8px; }
p, li { font-size: 15px; }
strong { color: #eef2f8; }
a { color: #0da2e7; }
code { background: #141829; border: 1px solid #232c44; border-radius: 5px;
       padding: 1px 5px; font-size: 13px; color: #9ecbff;
       overflow-wrap: anywhere; }
pre { background: #10131f; border: 1px solid #232c44; border-radius: 8px;
      padding: 14px 16px; overflow-x: auto; }
pre code { border: none; background: none; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 14px 0 20px; }
th, td { border: 1px solid #232c44; padding: 7px 10px; font-size: 13.5px;
         text-align: left; vertical-align: top; overflow-wrap: anywhere; }
th { background: #141829; color: #fff; }
tr:nth-child(even) td { background: #0f1220; }
img { max-width: 100%; box-sizing: border-box; border-radius: 10px;
      border: 1px solid #232c44; margin: 10px 0 2px; }
em { color: #8b95a8; }
hr { border: none; border-top: 1px solid #1d2435; margin: 36px 0; }
@media (max-width: 640px) { body { padding: 28px 16px 64px; }
  h1 { font-size: 25px; } h2 { font-size: 20px; }
  th, td { padding: 5px 7px; }
  table { display: block; overflow-x: auto; }
  thead, tbody { display: table; width: 100%; } }
"""


def embed_images(html: str, base: pathlib.Path) -> str:
    def repl(m: re.Match) -> str:
        src = m.group(1)
        if src.startswith(("http:", "https:", "data:")):
            return m.group(0)
        p = (base / src).resolve()
        if not p.exists():
            print(f"warning: missing image {p}")
            return m.group(0)
        data = base64.b64encode(p.read_bytes()).decode()
        return f'src="data:image/png;base64,{data}"'
    return re.sub(r'src="([^"]+)"', repl, html)


def main() -> int:
    src = pathlib.Path(sys.argv[1])
    out = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".html")
    text = src.read_text()
    body = markdown.markdown(
        text, extensions=["tables", "fenced_code", "sane_lists"])
    body = embed_images(body, src.parent)
    # the document's own H1 beats the file name, which is often just README
    heading = next((line[2:].strip() for line in text.splitlines()
                    if line.startswith("# ")), "")
    title = heading or src.stem.replace("-", " ")
    html = (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width, initial-scale=1'>"
            f"<title>{title}</title><style>{CSS}</style></head>"
            f"<body><main>{body}</main></body></html>")
    out.write_text(html)
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
