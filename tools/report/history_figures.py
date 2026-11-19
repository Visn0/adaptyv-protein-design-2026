#!/usr/bin/env python3
"""Build the figures for a challenge's complete-history document.

Input:  <challenge>/docs/figures/figure-spec.json
Output: <challenge>/docs/figures/funnel-pipeline.png   the pipeline funnel
        <challenge>/docs/figures/<slug>.png            a strip of Mol* panels

Both figures are HTML pages screenshotted with headless Chromium, so they
carry the same typography as the document itself. The molecular panels reuse
the structures already committed inside viewers/multiview/*.html (the
`const ITEMS = [...]` array), so nothing outside the repo is needed.

Usage: python3 tools/report/history_figures.py challenges/04-tfr1 [--only funnel|panels]
Needs Pillow for the funnel crop: ~/.venvs/genie3/bin/python works.
"""

from __future__ import annotations

import argparse
import io
import json
import pathlib
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def esc(text: str) -> str:
    """Local, because tools/report/html.py shadows the stdlib html module."""
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))

from tools.report.molstar_views import find_chrome  # noqa: E402
from tools.serve import molstar_viewer  # noqa: E402

FONT = ('"Geist", system-ui, -apple-system, "Segoe UI", sans-serif')
BG = "#0b0c14"
TONES = {
    "green": ("#07261a", "#10b981", "#34d399"),
    "orange": ("#2a1c07", "#f59e0b", "#fbbf24"),
    "pink": ("#2a0a1a", "#ec4899", "#f472b6"),
    "blue": ("#071d2a", "#38bdf8", "#7dd3fc"),
}
PANEL_W = 800            # one Mol* panel; 3 panels = a 2400-wide strip
PANEL_SHOT_H = 900       # shot tall: Mol*'s own side panel intrudes on a short window
PANEL_VIS_H = 700        # of which this much is kept (drops the empty floor)
PANEL_CROP_TOP = 110     # cropped off the top of each shot
BINDER = 0xe879f9        # magenta, as in the challenge-5 figures
BARE_CSS = ("#head, #leftbar, #rightbar, #expand, #legend, #hoverlabel, "
            "#caption { display: none !important; }")
BANNER_H = 66


# --------------------------------------------------------------- screenshots
def shot(chrome: str, page: pathlib.Path, png: pathlib.Path,
         width: int, height: int, budget_ms: int = 25000) -> None:
    """One headless screenshot of a local page. Retries: WebGL can be slow."""
    last = ""
    for _ in range(3):
        png.unlink(missing_ok=True)
        try:
            subprocess.run(
                # old headless: --headless=new + swiftshader loses WebGL here
                [chrome, "--headless", "--no-sandbox", "--disable-gpu",
                 f"--window-size={width},{height}",
                 f"--virtual-time-budget={budget_ms}",
                 f"--screenshot={png}", "--hide-scrollbars", f"file://{page}"],
                check=True, capture_output=True, timeout=budget_ms / 1000 + 90)
        except Exception as exc:              # a slow render must be retried
            last = str(exc)[:200]
            continue
        if png.exists() and png.stat().st_size > 15000:
            return
        last = f"png too small ({png.stat().st_size if png.exists() else 0} bytes)"
    raise SystemExit(f"screenshot failed after 3 attempts: {page}: {last}")


def crop_background(png: pathlib.Path) -> None:
    """Trim the dead page background below the content."""
    from PIL import Image

    im = Image.open(png).convert("RGB")
    bg = im.getpixel((2, im.height - 2))
    px = im.load()
    last = im.height - 1
    while last > 0:
        row = range(0, im.width, 7)
        if any(px[x, last] != bg for x in row):
            break
        last -= 1
    if last >= im.height - 2:
        print(f"WARNING: {png.name} fills the window - the funnel is taller "
              f"than {im.height}px and is cut off; raise the shot height")
    im.crop((0, 0, im.width, min(im.height, last + 40))).save(png)


# -------------------------------------------------------------- funnel figure
def _chip(text: str, tone: str) -> str:
    bg, border, fg = TONES.get(tone, TONES["blue"])
    return (f'<span class="chip" style="background:{bg};border-color:{border};'
            f'color:{fg}">{esc(text)}</span>')


def funnel_html(spec: dict) -> str:
    f = spec["funnel"]
    gen = f["generation"]
    total = sum(s["count"] for s in gen["slices"]) or 1

    bar, legend = [], []
    for s in gen["slices"]:
        pct = max(5.5, 100.0 * s["count"] / total)  # a tiny slice still needs its label
        # flex-grow (not a % basis): the 3px gaps then cannot overflow the row
        bar.append(f'<div class="seg" style="flex:{pct:.2f} 1 0;'
                   f'background:{s["color"]}">{esc(s["label"])}</div>')
        legend.append(f'<span class="leg"><i style="background:{s["color"]}">'
                      f'</i>{esc(s["legend"])}</span>')

    rows = []
    for step in f["steps"]:
        if step["kind"] == "result":
            rows.append(
                f'<div class="arrow">&#9660;</div>'
                f'<div class="result"><div class="rh">'
                f'{esc(step["heading"])}</div>'
                f'<div class="rs">{esc(step.get("sub", ""))}</div></div>')
        else:
            chip = _chip(step["cost"], step.get("tone", "blue")) if step.get("cost") else ""
            rows.append(
                f'<div class="arrow">&#9660;</div>'
                f'<div class="filter"><b>{esc(step["title"])}</b> - '
                f'{esc(step["text"])} {chip}</div>')

    final = f["final"]
    note = f.get("note")
    note_html = ""
    if note:
        note_html = (f'<div class="note"><b>{esc(note["title"])}</b> '
                     f'{esc(note["text"])}</div>')

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
  html,body {{ margin:0; background:{BG}; color:#cbd2dd; font-family:{FONT}; }}
  main {{ width:1420px; margin:0 auto; padding:28px 0 20px; }}
  h1 {{ color:#fff; font-size:30px; margin:0 0 6px; }}
  .sub {{ color:#8b93a7; font-size:14px; margin:0 0 20px; }}
  .card {{ background:#121829; border:1px solid #1d2435; border-radius:10px;
           padding:16px 18px; }}
  .gh {{ color:#fff; font-size:20px; font-weight:700; text-align:center; }}
  .gs {{ color:#8b93a7; font-size:13px; text-align:center; margin:4px 0 14px; }}
  .bar {{ display:flex; gap:3px; }}
  .seg {{ color:#0b0c14; font-size:12px; font-weight:700; text-align:center;
          padding:5px 2px; border-radius:4px; overflow:hidden;
          white-space:nowrap; text-overflow:ellipsis; }}
  .legend {{ margin-top:10px; display:flex; flex-wrap:wrap; gap:16px; }}
  .leg {{ color:#8b93a7; font-size:12px; display:flex; align-items:center; }}
  .leg i {{ width:9px; height:9px; border-radius:2px; margin-right:6px;
            display:inline-block; }}
  .arrow {{ color:#38bdf8; text-align:center; font-size:15px; margin:7px 0; }}
  .filter {{ background:#0e1320; border:1px solid #1d2435; border-radius:8px;
             padding:12px 14px; font-size:13.5px; line-height:1.6; }}
  .filter b {{ color:#eef2f8; }}
  .result {{ background:#121829; border:1px solid #1d2435; border-radius:10px;
             padding:12px 18px; margin:0 160px; text-align:center; }}
  .rh {{ color:#fff; font-size:19px; font-weight:700; }}
  .rs {{ color:#8b93a7; font-size:13px; margin-top:3px; }}
  .final {{ background:#0d1b2b; border:2px solid #38bdf8; border-radius:10px;
            padding:14px 18px; margin:0 300px; text-align:center; }}
  .note {{ margin-top:22px; background:#140d22; border-left:3px solid #a855f7;
           border-radius:6px; padding:12px 16px; font-size:13px;
           line-height:1.6; }}
  .note b {{ color:#d8b4fe; }}
  .chip {{ font-size:11.5px; font-weight:700; border:1px solid; border-radius:
           999px; padding:3px 9px; white-space:nowrap; }}
</style></head><body><main>
  <h1>{esc(f["title"])}</h1>
  <p class="sub">{esc(f["subtitle"])}</p>
  <div class="card">
    <div class="gh">{esc(gen["heading"])}</div>
    <div class="gs">{esc(gen["sub"])}</div>
    <div class="bar">{''.join(bar)}</div>
    <div class="legend">{''.join(legend)}</div>
  </div>
  {''.join(rows)}
  <div class="arrow">&#9660;</div>
  <div class="final"><div class="rh">{esc(final["heading"])}</div>
    <div class="rs">{esc(final.get("sub", ""))}</div></div>
  {note_html}
</main></body></html>"""


# ----------------------------------------------------------- molecular panels
def load_items(page: pathlib.Path) -> dict:
    text = page.read_text()
    i = text.find("const ITEMS = ")
    if i < 0:
        raise SystemExit(f"no ITEMS array in {page}")
    i += len("const ITEMS = ")
    items, _ = json.JSONDecoder().raw_decode(text[i:])
    return {it["id"]: it for it in items}


TARGET_COLORS = [0x0099ff, 0x00d2ff, 0x9ca3af, 0x60a5fa]   # per target chain


def fold_items(panel: dict) -> list:
    """Items straight from one Boltz fold directory.

    Use this when a challenge's committed viewer page places each design in
    its own fold frame (02-tnfa does: its builder takes the target from the
    first design only and superposes nothing, so every other design floats
    into the target). One fold is internally consistent by construction.
    """
    import numpy as np
    from Bio.PDB import MMCIFParser, PDBIO, Select

    path = pathlib.Path(panel["source_fold"]).expanduser()
    model_n = panel.get("model", 0)
    hits = sorted(path.glob(f"**/*_model_{model_n}.cif"))
    if not hits:
        raise SystemExit(f"no model {model_n} under {path}")
    st = MMCIFParser(QUIET=True).get_structure("m", str(hits[0]))[0]
    bid = panel.get("binder_chain", "A")

    def pdb_of(keep):
        class Keep(Select):
            def accept_chain(self, c):
                return 1 if c.id in keep else 0
        buf, io_ = io.StringIO(), PDBIO()
        io_.set_structure(st)
        io_.save(buf, Keep())
        return buf.getvalue()

    target_ids = [c.id for c in st if c.id != bid]
    coords = np.array([a.get_coord() for a in st[bid].get_atoms()])
    center = coords.mean(axis=0)
    focus = {"center": [round(float(v), 2) for v in center],
             "radius": round(float(np.linalg.norm(coords - center, axis=1).max()) + 14, 1)}
    colors = {c: TARGET_COLORS[i % len(TARGET_COLORS)]
              for i, c in enumerate(target_ids)}
    return [
        {"id": "target", "label": panel.get("target_label", "target"),
         "color": colors[target_ids[0]], "pdb": pdb_of(set(target_ids)),
         "chains": target_ids, "chainColors": colors, "interface": [],
         "on": True, "scores": {}},
        {"id": "binder", "label": panel["label"], "color": BINDER,
         "pdb": pdb_of({bid}), "chains": [bid], "chainColors": {bid: BINDER},
         "interface": [], "focus": focus, "on": True, "scores": {}},
    ]


def _ca(pdb_text: str) -> dict:
    """(chain, resseq) -> CA coordinate."""
    out = {}
    for line in pdb_text.splitlines():
        if line.startswith("ATOM") and line[12:16].strip() == "CA":
            out[(line[21], line[22:27])] = (
                float(line[30:38]), float(line[38:46]), float(line[46:54]))
    return out


def align_transform(moving_pdb: str, fixed_pdb: str):
    """Kabsch rotation+translation putting `moving` into `fixed`'s frame.

    Viewer pages built at different times hold the same target in different
    frames, so panels taken from two pages are not comparable until one is
    rotated onto the other.
    """
    import numpy as np

    a, b = _ca(moving_pdb), _ca(fixed_pdb)
    keys = sorted(set(a) & set(b))
    if len(keys) < 20:
        raise SystemExit(f"cannot align: only {len(keys)} shared CA atoms")
    P = np.array([a[k] for k in keys])
    Q = np.array([b[k] for k in keys])
    pc, qc = P.mean(0), Q.mean(0)
    U, _, Vt = np.linalg.svd((P - pc).T @ (Q - qc))
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, d]) @ U.T
    rms = float(np.sqrt((((P - pc) @ R.T + qc - Q) ** 2).sum(1).mean()))
    if rms > 8.0:
        raise SystemExit(f"superposition RMSD {rms:.1f} A over {len(keys)} CA: "
                         f"these pages do not hold the same target")
    return R, qc - pc @ R.T, rms


def transform_pdb(pdb_text: str, R, t) -> str:
    import numpy as np

    out = []
    for line in pdb_text.splitlines():
        if line.startswith(("ATOM", "HETATM")):
            xyz = np.array([float(line[30:38]), float(line[38:46]),
                            float(line[46:54])]) @ R.T + t
            line = (line[:30] + "".join(f"{v:8.3f}" for v in xyz) + line[54:])
        out.append(line)
    return "\n".join(out) + "\n"


def target_pdb(ch: pathlib.Path, panel: dict) -> str:
    """The panel's target structure - its id is not always plain 'target'."""
    items = load_items(ch / panel["source_page"])
    for item_id in panel["item_ids"]:
        if item_id.startswith("target"):
            return items[item_id]["pdb"]
    raise SystemExit(f"{panel['source_page']}: no target item among "
                     f"{panel['item_ids']} to align on")


def build_panel_page(ch: pathlib.Path, slug: str, panel: dict,
                     focus: dict | None = None,
                     xform=None) -> pathlib.Path:
    """One viewer page holding just this panel's structures."""
    if panel.get("source_fold"):
        if focus or xform is not None:
            raise SystemExit(
                f"{slug}: share_focus/align_to_first need a common frame, and "
                f"a source_fold panel brings its own - split the figure")
        picked = fold_items(panel)
        out = ch / "viewers" / "multiview" / f"fig-{slug}.html"
        page = molstar_viewer.render_viewer_page(
            picked, title=panel["label"], label=panel["label"],
            slug=f"fig-{slug}", binder_chain=panel.get("binder_chain", "A"))
        out.write_text(page.replace("</head>", f"<style>{BARE_CSS}</style></head>", 1))
        return out

    src = ch / panel["source_page"]
    items = load_items(src)
    picked = []
    for item_id in panel["item_ids"]:
        if item_id not in items:
            raise SystemExit(f"{src.name}: no item {item_id!r} "
                             f"(have {sorted(items)[:8]} ...)")
        it = dict(items[item_id])
        it["on"] = True
        # the viewer hides anything not on the current species tab, and that
        # tab always starts on human: a mouse-only panel would render empty
        it.pop("species", None)
        if not item_id.startswith("target"):
            # one binder colour across every figure: a design must never come
            # out in the same hue as the target chain it sits on
            it["color"] = BINDER
            it["chainColors"] = {c: BINDER for c in it.get("chains", [])}
            if focus:            # share_focus: one camera across the panels
                it["focus"] = focus
        if xform is not None:
            it["pdb"] = transform_pdb(it["pdb"], *xform)
        picked.append(it)
    out = ch / "viewers" / "multiview" / f"fig-{slug}.html"
    page = molstar_viewer.render_viewer_page(
        picked, title=panel["label"], label=panel["label"], slug=f"fig-{slug}",
        binder_chain=(panel.get("focus_chains") or ["A"])[0])
    # the page is only ever screenshotted, so its interactive chrome is noise
    page = page.replace("</head>", f"<style>{BARE_CSS}</style></head>", 1)
    out.write_text(page)
    return out


def strip_html(panels: list[dict], shots: list[pathlib.Path]) -> str:
    cells = []
    for panel, png in zip(panels, shots):
        sub = panel.get("sub", "")
        cells.append(
            f'<div class="cell"><div class="t">{esc(panel["label"])}</div>'
            f'<div class="s">{esc(sub)}</div>'
            f'<div class="shot"><img src="file://{png}" width="{PANEL_W}" '
            f'height="{PANEL_SHOT_H}"></div></div>')
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
  html,body {{ margin:0; background:{BG}; font-family:{FONT}; }}
  .row {{ display:flex; }}
  .cell {{ width:{PANEL_W}px; }}
  .t {{ color:#fff; font-size:21px; font-weight:700; padding:12px 14px 0;
        white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .s {{ color:#8b93a7; font-size:13px; padding:2px 14px 8px; height:18px;
        white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .shot {{ height:{PANEL_VIS_H}px; overflow:hidden; }}
  /* the viewer's own header and the empty floor are cropped away */
  img {{ display:block; margin-top:-{PANEL_CROP_TOP}px; }}
</style></head><body><div class="row">{''.join(cells)}</div></body></html>"""


# ----------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("challenge", help="challenge directory, e.g. challenges/04-tfr1")
    ap.add_argument("--only", choices=["funnel", "panels"])
    args = ap.parse_args()

    ch = (REPO / args.challenge).resolve()
    figdir = ch / "docs" / "figures"
    spec = json.loads((figdir / "figure-spec.json").read_text())
    chrome = find_chrome()
    # intermediates (panel shots, the funnel page) are rebuilt from the spec
    # every run, so they stay out of the repo
    scratch = pathlib.Path(tempfile.mkdtemp(prefix="history-figures-"))

    if args.only != "panels" and spec.get("funnel"):
        page = scratch / "funnel.html"
        page.write_text(funnel_html(spec))
        png = figdir / "funnel-pipeline.png"
        shot(chrome, page, png, 1500, 2600, budget_ms=8000)
        crop_background(png)
        print(f"wrote {png}")

    if args.only != "funnel":
        for fig in spec.get("molecular_figures", []):
            shots = []
            # share_focus: panels that compare the same site need one camera
            focus = None
            if fig.get("share_focus") or fig.get("align_to_first"):
                if any(p.get("source_fold") for p in fig["panels"]):
                    raise SystemExit(f"{fig['slug']}: share_focus and "
                                     f"align_to_first need source_page panels")
            if fig.get("share_focus"):
                first = fig["panels"][0]
                items = load_items(ch / first["source_page"])
                focus = next(items[i]["focus"] for i in first["item_ids"]
                             if not i.startswith("target") and items[i].get("focus"))
            ref_target = None
            if fig.get("align_to_first"):
                ref_target = target_pdb(ch, fig["panels"][0])
            for n, panel in enumerate(fig["panels"]):
                xform = None
                if ref_target is not None and n > 0:
                    mine = target_pdb(ch, panel)
                    R, t, rms = align_transform(mine, ref_target)
                    print(f"   aligned panel {n} onto panel 0: "
                          f"RMSD {rms:.2f} A")
                    xform = (R, t)
                page = build_panel_page(ch, f"{fig['slug']}-{n}", panel,
                                        focus, xform)
                png = scratch / f"{fig['slug']}-{n}.png"
                shot(chrome, page, png, PANEL_W, PANEL_SHOT_H)
                shots.append(png)
            strip = scratch / f"{fig['slug']}-strip.html"
            strip.write_text(strip_html(fig["panels"], shots))
            out = figdir / f"{fig['slug']}.png"
            shot(chrome, strip, out,
                 PANEL_W * len(shots), PANEL_VIS_H + BANNER_H, budget_ms=6000)
            print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
