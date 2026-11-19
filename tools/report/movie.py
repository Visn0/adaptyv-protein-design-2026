"""MP4 movies of one structure from a run (headless Chrome + ffmpeg).

Five modes:
    trajectory  real physics playback: frames of an all-atom MD trajectory
                (a multi-model PDB from the md pipeline). This is the one
                movie mode with a real force field behind it.
    sim   coarse-grained physics mode. A Langevin simulation of the binder
          against its target, driven by the design's measured pH-linkage wells
          (see tools.report.sim for the model rules and the honesty notes).
    dock  scripted preview: the binder slides onto its predicted pose. No
          physics. Kept for runs without linkage scores.
    spin  the complex turns around the Y axis. Geometry only.
    auto  picks trajectory for a multi-model structure, else sim when a binder
          chain and linkage scores exist, else dock, else spin.

Three styles: cartoon (ribbons), cloud (one dot per atom) and surface.

Every movie carries an overlay: a title, a colour legend, a bottom caption
with the model notes, and (sim only) a live HUD with pH, well depths,
distance, occupancy and a well-curve inset. The honesty text rides with the
video, so a shared file cannot lose it.

    pdt movie <run-dir> [--mode auto|trajectory|sim|dock|spin] [--style cartoon|surface]
                        [--design NAME] [--seed N]

Requires Google Chrome and ffmpeg on PATH.
"""
from __future__ import annotations

import html as _html
import json
import math
import os
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from tools.md import analyze
from tools.report import sim as sim_mod
from tools.serve import app as serve_app

CHROME = os.environ.get("PDT_CHROME") or "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BINDER_PINK = "#e879f9"
DUM = "DUM"
FONT_FILES = ("geist-400.woff2", "geist-500.woff2", "geist-600.woff2",
              "geist-mono-400.woff2", "geist-mono-500.woff2")

PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
@font-face { font-family: 'Geist'; src: url('geist-400.woff2') format('woff2'); font-weight: 400; }
@font-face { font-family: 'Geist'; src: url('geist-500.woff2') format('woff2'); font-weight: 500; }
@font-face { font-family: 'Geist'; src: url('geist-600.woff2') format('woff2'); font-weight: 600; }
@font-face { font-family: 'Geist Mono'; src: url('geist-mono-400.woff2') format('woff2'); font-weight: 400; }
@font-face { font-family: 'Geist Mono'; src: url('geist-mono-500.woff2') format('woff2'); font-weight: 500; }
html, body { margin: 0; background: #0b0f14; width: __W__px; height: __H__px; overflow: hidden;
             font-family: 'Geist', system-ui, sans-serif; color: #d4d4d8; }
#v { position: absolute; inset: 0; }
.panel { position: absolute; background: rgba(10, 13, 19, .74); border: 1px solid rgba(255,255,255,.09);
         border-radius: 12px; padding: 12px 14px; }
#title { left: 16px; top: 14px; max-width: 640px; }
#title h1 { margin: 0; font-size: 16.5px; font-weight: 600; letter-spacing: -.2px; }
#title .sub { margin-top: 3px; font-size: 11.5px; color: #9ca3af; }
#legend { left: 16px; top: 76px; }
#legend .row { display: flex; align-items: center; gap: 8px; font-size: 12px; margin: 4px 0; }
#legend .dot { width: 10px; height: 10px; border-radius: 3px; flex: none; }
#legend .what { color: #cbd2dd; }
#hud { right: 16px; top: 14px; width: 240px; }
#hud .ph { font-family: 'Geist Mono', monospace; font-size: 24px; font-weight: 500; letter-spacing: -.5px; }
#hud .ph small { font-size: 10.5px; color: #9ca3af; margin-left: 8px; letter-spacing: .02em;
                 font-family: 'Geist', sans-serif; }
#hud .row { display: flex; justify-content: space-between; font-size: 11.5px; margin: 5px 0; color: #cbd2dd; }
#hud .row .k { color: #9ca3af; }
#hud .row .v { font-family: 'Geist Mono', monospace; }
#hud .bar { margin-top: 8px; background: rgba(255,255,255,.08); border-radius: 5px; height: 7px; overflow: hidden; }
#hud .bar i { display: block; height: 100%; background: #34d399; border-radius: 5px; }
#hud .barlabel { font-size: 10.5px; color: #9ca3af; margin-top: 5px; display: flex; justify-content: space-between; }
#hud .state { margin-top: 9px; font-family: 'Geist Mono', monospace; font-size: 11px; letter-spacing: .06em; }
.state.free { color: #93a1b5; }
.state.contact { color: #34d399; }
#switchbadge { display: inline-block; margin-top: 9px; font-family: 'Geist Mono', monospace; font-size: 10.5px;
               color: #f59e0b; border: 1px solid rgba(245,158,11,.45); background: rgba(245,158,11,.1);
               border-radius: 999px; padding: 2px 9px; letter-spacing: .08em; }
#inset { right: 16px; bottom: 16px; padding: 10px 12px 4px; }
#inset .barlabel { font-size: 9.5px; color: #87909f; display: flex; justify-content: space-between;
                   margin-top: 2px; }
#zoom { right: 16px; top: 230px; width: 372px; padding: 10px 12px 8px; }
#zoomv { width: 100%; height: 264px; }
#zoom .zlabel { font-size: 10.5px; color: #87909f; display: flex; justify-content: space-between; margin-top: 6px; }
#zoom .zlabel b { color: #fbbf24; font-weight: 500; }
#caption { left: 16px; bottom: 16px; right: 306px; padding: 10px 14px; }
#caption .line { font-size: 11.5px; color: #cbd2dd; margin: 2px 0; }
#caption .dim { font-size: 10.5px; color: #87909f; margin: 3px 0 1px; }
</style></head>
<body><div id="v"></div>
<script src="3Dmol-min.js"></script>
<div class="panel" id="title"><h1>__TITLE__</h1><div class="sub">__SUBTITLE__</div></div>
<div class="panel" id="legend">__LEGEND__</div>
__HUD__
__INSET__
<div class="panel" id="caption">__CAPTION__</div>
<script>
const structure = __STRUCTURE__;
const zoomStructure = __ZOOM_STRUCTURE__;
const config = __CONFIG__;
const viewer = $3Dmol.createViewer(document.getElementById("v"), {backgroundColor: "#0b0f14"});
window.__surface_done = false;
var _surfacePromise = null;
viewer.addModel(structure, __FMT__);
if (config.style === "cloud") {
  // point cloud: one small dot per atom; chains keep their colours
  viewer.setStyle({}, {sphere: {radius: 0.26, color: "#6b7686"}});
  (config.highlights || []).forEach(function(hint) {
    hint.sels.forEach(function(sel) {
      viewer.setStyle(sel, {sphere: {color: hint.color,
                                     radius: hint.repr === "cartoon" ? 0.34 : 0.55}});
    });
  });
} else if (config.style === "surface") {
  // surface only: the smooth molecular surface carries the shape; highlights stay on top
  (config.highlights || []).forEach(function(hint) {
    hint.sels.forEach(function(sel) {
      if (hint.repr === "cartoon") {
        viewer.setStyle(sel, {cartoon: {color: hint.color}});
      } else {
        viewer.setStyle(sel, {stick: {color: hint.color, radius: 0.15}});
        viewer.setStyle(sel, {sphere: {color: hint.color, scale: 0.35}});
      }
    });
  });
  viewer.addSurface($3Dmol.SurfaceType.SAS, {opacity: 0.75, color: "#5f6f86"});
} else if (config.style === "cartoon+cloud") {
  // cartoon ribbons with a translucent one-dot-per-atom cloud on top.
  // Ribbon and cloud share one chain colour map built from the cartoon hints,
  // so no second cartoon layer ever overlaps the first.
  var chainMap = {};
  (config.highlights || []).forEach(function(hint) {
    if (hint.repr === "cartoon") {
      hint.sels.forEach(function(sel) {
        if (sel.chain) { chainMap[sel.chain] = hint.color; }
      });
    }
  });
  var chains = Object.keys(chainMap);
  var scheme = chains.length ? {prop: "chain", map: chainMap} : "chain";
  viewer.setStyle({}, {cartoon: {colorscheme: scheme}});
  // one sphere per atom, mostly opaque: the protein form reads as a body,
  // the ribbons show through the gaps. Only the mapped chains get spheres —
  // the invisible camera-anchor atoms (chain Z) must never render.
  viewer.addStyle(chains.length ? {chain: chains} : {},
                  {sphere: {colorscheme: scheme, radius: 0.5, opacity: 0.9}});
  (config.highlights || []).forEach(function(hint) {
    if (hint.repr === "cartoon") { return; }
    hint.sels.forEach(function(sel) {
      viewer.addStyle(sel, {stick: {color: hint.color, radius: 0.15}});
      viewer.addStyle(sel, {sphere: {color: hint.color, scale: 0.32}});
    });
  });
} else if (config.style === "surface+cartoon") {
  // translucent exterior surface over cartoon ribbons; hotspot residues (and
  // the target patch around the binder footprint) carry their own surface
  // colour, so the binding area reads at a glance
  var chainMap = {};
  var hotspot = {};
  var binderChain = null;
  (config.highlights || []).forEach(function(hint) {
    hint.sels.forEach(function(sel) {
      if (hint.repr === "cartoon") {
        if (sel.chain) {
          chainMap[sel.chain] = hint.color;
          if (hint.color === "#e879f9") { binderChain = sel.chain; }
        }
      } else if (sel.chain && sel.resi !== undefined) {
        hotspot[sel.resi + ":" + sel.chain] = true;
      }
    });
  });
  (config.patch || []).forEach(function(tok) { hotspot[tok[0] + ":" + tok[1]] = true; });
  var chains = Object.keys(chainMap);
  var scheme = chains.length ? {prop: "chain", map: chainMap} : "chain";
  viewer.setStyle({}, {cartoon: {colorscheme: scheme}});
  viewer.addSurface($3Dmol.SurfaceType.SAS, {opacity: 0.62, colorfunc: function(atom) {
    if (hotspot[atom.resi + ":" + atom.chain]) { return "#fbbf24"; }
    if (binderChain && atom.chain === binderChain) { return "#e879f9"; }
    return "#7f8aa0";
  }}, chains.length ? {chain: chains} : {}).then(function() { window.__surface_done = true; viewer.render(); })
    .catch(function() { window.__surface_done = true; });
  (config.highlights || []).forEach(function(hint) {
    if (hint.repr === "cartoon") { return; }
    hint.sels.forEach(function(sel) {
      viewer.addStyle(sel, {stick: {color: hint.color, radius: 0.15}});
      viewer.addStyle(sel, {sphere: {color: hint.color, scale: 0.32}});
    });
  });
} else {
  viewer.setStyle({}, {cartoon: {colorscheme: "chain"}});
  (config.highlights || []).forEach(function(hint) {
    hint.sels.forEach(function(sel) {
      if (hint.repr === "cartoon") {
        viewer.setStyle(sel, {cartoon: {color: hint.color}});
      } else {
        viewer.setStyle(sel, {stick: {color: hint.color, radius: 0.15}});
        viewer.setStyle(sel, {sphere: {color: hint.color, scale: 0.32}});
      }
    });
  });
}
viewer.setStyle({resn: "DUM"}, {});  // empty style = no representation; the camera anchors never render
viewer.zoomTo();
if (config.angle) { viewer.rotate(config.angle, "y"); }
if (config.bridge) {
  viewer.addCylinder({start: {x: config.bridge[0], y: config.bridge[1], z: config.bridge[2]},
                      end: {x: config.bridge[3], y: config.bridge[4], z: config.bridge[5]},
                      radius: 0.3, dashed: true, color: "#34d399", opacity: 0.9});
}
viewer.render();
if (config.zoom && zoomStructure) {
  // the hot-zone inset: interface residues as ball+stick with dashed lines
  // between the closest contacting atoms, framed by the zoom anchors
  var zdiv = document.getElementById("zoomv");
  if (zdiv) {
    var zviewer = $3Dmol.createViewer(zdiv, {backgroundColor: "#0b0f14"});
    zviewer.addModel(zoomStructure, __FMT__);
    zviewer.setStyle({}, {});
    (config.highlights || []).forEach(function(hint) {
      if (hint.repr === "cartoon") { return; }
      hint.sels.forEach(function(sel) {
        var zc = chainMap[sel.chain] || hint.color;
        zviewer.addStyle(sel, {stick: {color: zc, radius: 0.13}});
        zviewer.addStyle(sel, {sphere: {color: zc, scale: 0.26}});
      });
    });
    (config.contacts || []).forEach(function(pair) {
      var A = zviewer.selectedAtoms({resi: pair.a[0], chain: pair.a[1]});
      var B = zviewer.selectedAtoms({resi: pair.b[0], chain: pair.b[1]});
      var bestA = null, bestB = null, bestD = 1e9;
      A.forEach(function(a) { B.forEach(function(b) {
        var dx = a.x - b.x, dy = a.y - b.y, dz = a.z - b.z;
        var d2 = dx * dx + dy * dy + dz * dz;
        if (d2 < bestD) { bestD = d2; bestA = a; bestB = b; }
      }); });
      if (bestA) {
        zviewer.addCylinder({start: {x: bestA.x, y: bestA.y, z: bestA.z},
                             end: {x: bestB.x, y: bestB.y, z: bestB.z},
                             radius: 0.1, dashed: true, color: "#fbbf24", opacity: 0.9});
      }
    });
    zviewer.setStyle({resn: "DUM"}, {});
    zviewer.zoomTo();
    zviewer.render();
  }
}
if (!(_surfacePromise && _surfacePromise.then)) { window.__surface_done = true; }
</script></body></html>"""


# ---------------------------------------------------------------- helpers

def _atoms(text: str):
    return [line for line in text.splitlines() if line.startswith(("ATOM", "HETATM"))]


def _xyz(line: str):
    return float(line[30:38]), float(line[38:46]), float(line[46:54])


def _centroid(lines) -> np.ndarray:
    coords = np.array([_xyz(line) for line in lines], dtype=float)
    return coords.mean(axis=0)


def _binder_chain(entry: dict) -> str | None:
    for hint in entry.get("highlights") or []:
        if hint.get("color") != BINDER_PINK:
            continue
        for selection in hint.get("selections") or []:
            token = str(selection).strip()
            if len(token) == 1 and token.isalnum():
                return token
    return None


def _legend_rows(entry: dict, binder: str | None) -> list:
    """(colour, label) rows for the on-video legend, from the viewer hints."""
    rows, seen = [], set()
    for hint in entry.get("highlights") or []:
        color = hint.get("color", "#f59e0b")
        tokens = [str(s).strip() for s in (hint.get("selections") or [])]
        if hint.get("repr") != "cartoon":
            label = "binding interface (ball+stick)"
        elif tokens and all(len(token) == 1 and token.isalnum() for token in tokens):
            if len(tokens) == 1:
                label = ("designed binder" if tokens[0] == binder else "target protein") \
                        + f" (chain {tokens[0]})"
            elif binder and binder in tokens:
                label = f"designed binder (chain {binder})"
            else:
                label = "target protein (chains " + ", ".join(tokens) + ")"
        else:
            label = "highlighted residues"
        key = (color, label)
        if key not in seen:
            seen.add(key)
            rows.append((color, label))
    return rows


def _legend_html(rows) -> str:
    cells = "".join(
        f'<div class="row"><span class="dot" style="background:{color}"></span>'
        f'<span class="what">{label}</span></div>'
        for color, label in rows
    )
    return cells or '<div class="row"><span class="what">structure view</span></div>'


def _caption_html(lines) -> str:
    """lines: (text, is_dim)."""
    return "".join(
        f'<div class="{"dim" if dim else "line"}">{_html.escape(text)}</div>'
        for text, dim in lines
    )


def _curve_value(curve, r: float) -> float:
    if not curve:
        return 0.0
    r = min(max(r, float(curve[0][0])), float(curve[-1][0]))
    return float(np.interp(r, [point[0] for point in curve], [point[1] for point in curve]))


def _well_inset(curve, current_r: float, contact_radius: float,
                width: int = 252, height: int = 126) -> str:
    """Small SVG: the well curve of the current pH plus the binder position."""
    pad_l, pad_r, pad_t, pad_b = 32, 10, 14, 20
    r_max = float(curve[-1][0]) if curve else 17.0
    y_lim = max(0.6, max(abs(value) for _r, value in curve) * 1.3) if curve else 0.6

    def sx(r):
        return pad_l + r / r_max * (width - pad_l - pad_r)

    def sy(value):
        return pad_t + (y_lim - value) / (2 * y_lim) * (height - pad_t - pad_b)

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
             f'font-family="Geist Mono, monospace">']
    zero_y = sy(0.0)
    parts.append(f'<line x1="{pad_l}" y1="{zero_y:.1f}" x2="{width - pad_r}" y2="{zero_y:.1f}" '
                 f'stroke="rgba(255,255,255,.25)" stroke-width="1"/>')
    edge_x = sx(contact_radius)
    parts.append(f'<line x1="{edge_x:.1f}" y1="{pad_t}" x2="{edge_x:.1f}" y2="{height - pad_b}" '
                 f'stroke="rgba(245,158,11,.55)" stroke-width="1" stroke-dasharray="3 3"/>')
    if curve:
        dots = " ".join(f"{sx(r):.1f},{sy(v):.1f}" for r, v in curve)
        parts.append(f'<polyline points="{dots}" fill="none" stroke="#0da2e7" stroke-width="1.8"/>')
        marker_y = sy(_curve_value(curve, current_r))
        parts.append(f'<circle cx="{sx(min(max(current_r, 0.0), r_max)):.1f}" cy="{marker_y:.1f}" '
                     f'r="3.4" fill="#e879f9" stroke="#0b0f14" stroke-width="1"/>')
    parts.append(f'<text x="4" y="{sy(y_lim) + 8:.1f}" font-size="9" fill="#87909f">{y_lim:+.2f}</text>')
    parts.append(f'<text x="4" y="{sy(-y_lim) + 2:.1f}" font-size="9" fill="#87909f">{-y_lim:+.2f}</text>')
    parts.append(f'<text x="4" y="{zero_y - 3:.1f}" font-size="9" fill="#87909f">0</text>')
    parts.append(f'<text x="{edge_x + 4:.1f}" y="{pad_t + 8}" font-size="9" fill="#f59e0b">contact edge</text>')
    parts.append("</svg>")
    return ('<div class="panel" id="inset">' + "".join(parts) +
            '<div class="barlabel"><span>distance from pose (A)</span>'
            '<span>well (kcal/mol)</span></div></div>')


# ------------------------------------------------------------- pose tools

def _axis_frame(binder_lines, target_lines):
    """Rotation that turns the binder->target axis screen-horizontal (+X)."""
    b = _centroid(binder_lines)
    t = _centroid(target_lines)
    u = b - t
    u = u / (np.linalg.norm(u) or 1.0)
    helper = np.array([0.0, 0.0, 1.0]) if abs(u[2]) < 0.9 else np.array([0.0, 1.0, 0.0])
    w = np.cross(u, helper)
    w = w / (np.linalg.norm(w) or 1.0)
    v = np.cross(w, u)
    return np.stack([u, v, w]), t  # rows: world -> rotated frame


def _rotate_text(text: str, rotation: np.ndarray, origin: np.ndarray) -> str:
    out = []
    for line in text.splitlines():
        if line.startswith(("ATOM", "HETATM")):
            point = rotation @ (np.array(_xyz(line)) - origin)
            line = line[:30] + f"{point[0]:8.3f}{point[1]:8.3f}{point[2]:8.3f}" + line[54:]
        out.append(line)
    return "\n".join(out)


def rotate_complex(text: str, binder_chain: str):
    """Turn the whole complex so the binder->target axis is +X.

    A fixed turn keeps the camera stable for every frame of the movie.
    """
    atoms = _atoms(text)
    binder_lines = [line for line in atoms if line[21] == binder_chain]
    target_lines = [line for line in atoms if line[21] != binder_chain]
    if not binder_lines or not target_lines:
        raise ValueError("the complex needs binder atoms and target atoms")
    rotation, origin = _axis_frame(binder_lines, target_lines)
    return _rotate_text(text, rotation, origin)


def _split_chains(text: str, binder_chain: str):
    atoms = _atoms(text)
    binder = [line for line in atoms if line[21] == binder_chain]
    target = [line for line in atoms if line[21] != binder_chain]
    return binder, target


def _offset_text(text: str, binder_chain: str, offset: np.ndarray) -> str:
    """Displace every binder atom by `offset` (an already-rotated complex)."""
    out = []
    for line in text.splitlines():
        if line.startswith(("ATOM", "HETATM")) and line[21] == binder_chain:
            x, y, z = _xyz(line)
            line = line[:30] + f"{x + offset[0]:8.3f}{y + offset[1]:8.3f}{z + offset[2]:8.3f}" + line[54:]
        out.append(line)
    return "\n".join(out)


def _interface_bridge(text: str, binder_chain: str, cutoff: float = 4.5):
    """Midpoints of the binder and target interface atoms (rotated text)."""
    binder, target = _split_chains(text, binder_chain)
    target_xyz = np.array([_xyz(line) for line in target])
    binder_hit, target_hit = [], []
    for line in binder:
        point = np.array(_xyz(line))
        distances = np.sqrt(((target_xyz - point) ** 2).sum(axis=1))
        nearest = distances.min()
        if nearest <= cutoff:
            binder_hit.append(point)
            target_hit.append(target_xyz[int(distances.argmin())])
    if not binder_hit:
        return None
    return np.array(binder_hit).mean(axis=0), np.array(target_hit).mean(axis=0)


def _anchor_lines(text: str, binder_chain: str, extra: float) -> str:
    """Invisible corner atoms that pin the camera for the whole movie.

    The target stays put, so its box is fixed. The binder box grows by
    `extra` on every side — the largest excursion of the simulation — so the
    camera fits every frame minute-for-minute and never drifts.
    """
    atoms = _atoms(text)
    target = np.array([_xyz(line) for line in atoms if line[21] != binder_chain])
    binder = np.array([_xyz(line) for line in atoms if line[21] == binder_chain])
    lo = np.minimum(target.min(axis=0), binder.min(axis=0) - extra)
    hi = np.maximum(target.max(axis=0), binder.max(axis=0) + extra)
    lines = []
    corners = [(lo[0], lo[1], lo[2]), (lo[0], lo[1], hi[2]), (lo[0], hi[1], lo[2]),
               (hi[0], lo[1], lo[2]), (lo[0], hi[1], hi[2]), (hi[0], lo[1], hi[2]),
               (hi[0], hi[1], lo[2]), (hi[0], hi[1], hi[2])]
    for serial, (x, y, z) in enumerate(corners, start=1):
        lines.append("HETATM %5d %-4s %3s %1s%4d    %8.3f%8.3f%8.3f  1.00 20.00           C  "
                     % (9000 + serial, "X", DUM, "Z", 1, x, y, z))
    return "\n".join(lines) + "\n"


# -------------------------------------------------------- design selection

def _load_design_metrics(run_dir: Path) -> dict:
    """name -> {selectivity, ddg_low, ddg_high} from the run's artifacts."""
    import pandas as pd

    table = {}
    for name, id_column in (("ph_scores.csv", "design"), ("mutant_metrics.csv", "mutant_id")):
        path = run_dir / "artifacts" / name
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        for _index, row in frame.iterrows():
            key = str(row.get(id_column, "")).strip()
            if not key or pd.isna(row.get("ph_selectivity_kcal")):
                continue
            table[key] = {
                "selectivity": float(row["ph_selectivity_kcal"]),
                "ddg_low": float(row.get("ddg_ph_low", float("nan"))),
                "ddg_high": float(row.get("ddg_ph_high", float("nan"))),
            }
    return table


def _resolve_design(metrics: dict, entry: dict, wanted: str | None):
    """(name, metrics) for the movie. Default: the entry's own design, else the
    most negative ('right direction') selectivity."""
    if not metrics:
        return None, None
    if wanted:
        if wanted in metrics:
            return wanted, metrics[wanted]
        matches = sorted(k for k in metrics if k.startswith(wanted))
        if not matches:
            raise SystemExit(f"unknown design {wanted!r} — available: "
                             f"{', '.join(sorted(metrics)[:8])} ...")
        return matches[0], metrics[matches[0]]
    stem = entry["path"].stem
    if stem in metrics:
        return stem, metrics[stem]
    matches = sorted(k for k in metrics if stem.startswith(k))
    if matches:
        best = max(matches, key=len)
        return best, metrics[best]
    name = min(metrics, key=lambda key: metrics[key]["selectivity"])
    return name, metrics[name]


def _ph_values(run_dir: Path) -> tuple:
    """(ph_low, ph_high) from the run spec when present, else the C1 defaults."""
    import yaml

    ph_low, ph_high = 6.5, 7.4
    spec_path = run_dir / "spec.resolved.yaml"
    if spec_path.exists():
        try:
            spec = yaml.safe_load(spec_path.read_text()) or {}
            params = spec.get("params") or {}
            ph_low = float(params.get("ph_low", ph_low))
            ph_high = float(params.get("ph_high", ph_high))
        except Exception:
            pass
    return ph_low, ph_high


# ------------------------------------------------------------- rendering

def _render_pages(pages: list, work: Path, width: int, height: int, workers: int,
                  wait_mode: str = "virtual") -> list:
    """Screenshot each page with headless Chrome; returns ordered PNG paths.

    wait_mode "virtual" uses a virtual-time budget (fast, fine for pages that
    render synchronously). "timeout" waits real seconds: molecular surfaces
    are computed in a web worker, and a virtual clock races past it.
    """
    pngs = [None] * len(pages)
    total = len(pages)
    started = time.time()
    state = {"done": 0}
    if wait_mode == "timeout":
        wait_flags = [f"--timeout={int(os.environ.get('PDT_MOVIE_TIMEOUT_MS', '12000'))}"]
    else:
        wait_flags = ["--virtual-time-budget=9000"]

    def one(index_page):
        index, page = index_page
        html_path = work / f"frame_{index:05d}.html"
        png_path = work / f"shot_{index:05d}.png"
        html_path.write_text(page)
        last_error = None
        for attempt in range(3):
            try:
                subprocess.run(
                    [CHROME, "--headless=new", "--no-sandbox", "--disable-gpu",
                     "--use-gl=swiftshader", "--enable-unsafe-swiftshader",
                     "--run-all-compositor-stages-before-draw",
                     f"--window-size={width},{height}"] + wait_flags +
                    [f"--screenshot={png_path}", "--hide-scrollbars",
                     f"file://{html_path}"],
                    check=True, capture_output=True,
                )
                last_error = None
                break
            except subprocess.CalledProcessError as exc:
                # headless Chrome fails transiently under load; retry a few times
                last_error = exc
                time.sleep(1.5 * (attempt + 1))
        if last_error is not None:
            raise SystemExit(f"chrome failed on frame {index}: {last_error.stderr[-400:]!r}")
        pngs[index] = png_path
        state["done"] += 1
        if state["done"] % 12 == 0 or state["done"] == total:
            rate = state["done"] / max(time.time() - started, 1e-6)
            print(f"  frame {state['done']}/{total} ({rate:.1f}/s)")

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        list(pool.map(one, list(enumerate(pages))))
    return pngs


# --------------------------------------------------------------- builders

def _build_page(pdb_text: str, fmt: str, config: dict, title: str, subtitle: str,
                rows, hud_html: str, inset_html: str, caption: str,
                width: int, height: int, zoom_structure: str | None = None) -> str:
    return (PAGE
            .replace("__W__", str(width))
            .replace("__H__", str(height))
            .replace("__TITLE__", _html.escape(title))
            .replace("__SUBTITLE__", _html.escape(subtitle))
            .replace("__LEGEND__", _legend_html(rows))
            .replace("__HUD__", hud_html)
            .replace("__INSET__", inset_html)
            .replace("__ZOOM_STRUCTURE__", json.dumps(zoom_structure) if zoom_structure else "null")
            .replace("__CAPTION__", caption)
            .replace("__STRUCTURE__", json.dumps(pdb_text))
            .replace("__CONFIG__", json.dumps(config))
            .replace("__FMT__", json.dumps(fmt)))


def _sim_pages(structure_text, binder_chain, entry, run_dir, design_name,
               design_metrics, highlights, rows, seed, width, height):
    """Frame pages for the simulation mode."""
    rotated = rotate_complex(structure_text, binder_chain)
    bridge = _interface_bridge(rotated, binder_chain)

    ph_low, ph_high = _ph_values(run_dir)
    selectivity = design_metrics["selectivity"]
    low, high = sim_mod.well_values_kcal(selectivity)
    wells = {ph_low: low, ph_high: high}
    schedule = [(ph_low, 0.45), (ph_high, 0.55)]
    params = sim_mod.SimParams(seed=seed if seed is not None else sim_mod.SimParams().seed)
    result = sim_mod.simulate(params, wells, schedule)
    max_excursion = max(frame.r for frame in result.frames)
    anchor = _anchor_lines(rotated, binder_chain, max_excursion + 2.0)

    title = design_name or entry["path"].stem
    stage = _html.escape(str(entry.get("stage", "")))
    subtitle = (f"conditional binding simulation · {stage} stage · run {run_dir.name} "
                f"· seed {params.seed}")
    ratio = math.exp(abs(sim_mod.kcal_to_kt(selectivity)))
    like_ph = ph_low if low < 0 else ph_high
    unlike_ph = ph_high if like_ph == ph_low else ph_low
    like_well = wells[like_ph]
    caption = _caption_html([
        ("Coarse-grained Langevin simulation of the binder against its target. "
         "Not all-atom MD.", False),
        (f"Well depth = half the measured pH selectivity ({selectivity:+.2f} kcal/mol): "
         f"favoured at pH {like_ph:g} (well {like_well:+.2f} kcal/mol), "
         f"disfavoured at pH {unlike_ph:g}. Ideal Ka ratio ~{ratio:.1f}x.", False),
        ("The absolute affinity is not measured. The linkage score ranks candidates; "
         "it does not predict real affinities.", False),
        ("Model time, not physical seconds. 1 kcal/mol = 1.69 kT at 298 K. "
         "Binder orientation is fixed at the docked pose.", True),
    ])

    switch_index = result.stats["phases"][0]["frames"]
    pages = []
    running = [0, 0]
    events = [0, 0]
    previous_contact = False
    for frame in result.frames:
        if frame.contact:
            running[frame.phase] += 1
            if not previous_contact:
                events[frame.phase] += 1
        previous_contact = frame.contact

        phase_start = 0 if frame.phase == 0 else switch_index
        frames_in_phase = frame.index - phase_start + 1
        fraction = running[frame.phase] / max(1, frames_in_phase)

        hud = ['<div class="panel" id="hud">']
        hud.append(f'<div class="ph">pH {frame.ph:g}<small>{_html.escape(str(entry.get("stage", "")))} stage</small></div>')
        hud.append(f'<div class="row"><span class="k">well at this pH</span>'
                   f'<span class="v">{frame.well_kcal:+.2f} kcal/mol</span></div>')
        hud.append(f'<div class="row"><span class="k">in kT</span>'
                   f'<span class="v">{sim_mod.kcal_to_kt(frame.well_kcal):+.2f} kT</span></div>')
        hud.append(f'<div class="row"><span class="k">distance from pose</span>'
                   f'<span class="v">{frame.r:.1f} A</span></div>')
        hud.append(f'<div class="bar"><i style="width:{min(100.0, fraction * 100.0):.1f}%"></i></div>')
        hud.append(f'<div class="barlabel"><span>contact occupancy this phase</span>'
                   f'<span>{fraction * 100.0:.0f}% · {events[frame.phase]} events</span></div>')
        state = "CONTACT" if frame.contact else "FREE"
        hud.append(f'<div class="state {"contact" if frame.contact else "free"}">state: {state}</div>')
        if 0 <= frame.index - switch_index < 12:
            hud.append('<span id="switchbadge">PH SWITCH</span>')
        hud.append("</div>")

        inset = _well_inset(result.curves.get(frame.ph), frame.r, params.contact_radius)
        bridge_coords = None
        if frame.contact and bridge is not None:
            binder_point = bridge[0] + frame.offset
            bridge_coords = [round(float(binder_point[0]), 3), round(float(binder_point[1]), 3),
                             round(float(binder_point[2]), 3),
                             round(float(bridge[1][0]), 3), round(float(bridge[1][1]), 3),
                             round(float(bridge[1][2]), 3)]
        pdb_text = _offset_text(rotated, binder_chain, frame.offset) + anchor
        config = {"highlights": highlights, "angle": None, "bridge": bridge_coords}
        pages.append(_build_page(pdb_text, "pdb", config, title, subtitle, rows,
                                 "".join(hud), inset, caption, width, height))

    meta_stats = {
        "design": design_name,
        "wells_kcal": wells,
        "wells_kt": {ph: round(sim_mod.kcal_to_kt(well), 3) for ph, well in wells.items()},
        "schedule": schedule,
        "params": {
            "n_frames": params.n_frames, "substeps": params.substeps,
            "step_rms": params.step_rms, "contact_radius": params.contact_radius,
            "box_radius": params.box_radius, "start_offset": params.start_offset,
            "seed": params.seed,
        },
        "phases": result.stats["phases"],
        "ideal_ka_ratio": round(ratio, 3),
        "note": ("Wells keep the measured selectivity S as "
                 "well(ph_low) - well(ph_high) = S. Occupancies emerge from the simulation."),
    }
    return pages, meta_stats


def _plain_pages(structure_text, binder_chain, entry, highlights, rows, fmt,
                 frames, mode, run_name, width, height, style: str = "cartoon"):
    """Frame pages for spin/dock, with legend and honest captions."""
    if mode == "dock" and binder_chain:
        rotated = rotate_complex(structure_text, binder_chain)
        anchor = _anchor_lines(rotated, binder_chain, 44.0)
        poses = _binder_pose_texts(rotated, binder_chain, steps=max(8, int(frames * 0.75)))
        specs = [(poses[0] + anchor, None)]
        specs += [(pose + anchor, None) for pose in poses[1:-1]]
        specs += [(poses[-1] + anchor, None)]
        caption = _caption_html([
            ("Scripted preview: the binder slides onto its predicted contact pose. "
             "This is an animation, not a simulation.", False),
            ("No physics runs in this clip. The physics view is --mode sim.", True),
        ])
        title = entry["path"].stem
        subtitle = f"scripted dock preview · run {run_name}"
    else:
        caption = _caption_html([
            ("Structure rotation — geometry only. No physics in this clip.", False),
        ])
        title = entry["path"].stem
        subtitle = f"static structure rotation · run {run_name}"
        specs = [(structure_text, step * (360.0 / max(1, frames)))
                 for step in range(frames)]

    pages = []
    for text, angle in specs:
        config = {"highlights": highlights, "angle": angle, "bridge": None,
                  "style": style}
        pages.append(_build_page(text, fmt, config, title, subtitle, rows,
                                 "", "", caption, width, height))
    return pages, {"mode": mode}


# ------------------------------------------------------- md trajectory mode

def _md_timing(run_dir: Path, entry: dict, model_count: int) -> tuple:
    """(duration_ns, step_ns) for a trajectory entry, from the md stage stats."""
    import re as _re

    state = entry["path"].stem
    match = _re.search(r"(low|high)", state)
    stem = state[:-len("_frames")] if state.endswith("_frames") else state
    stats_path = run_dir / "artifacts" / "md" / f"{match.group(1)}_stats.json" \
        if match else run_dir / "artifacts" / "md" / f"{stem}_stats.json"
    duration, step = 0.0, 0.0
    if stats_path is not None and stats_path.exists():
        try:
            data = json.loads(stats_path.read_text())
            duration = float(data.get("duration_ns") or 0.0)
            pool = int(data.get("n_frames") or model_count)
            per = duration / max(pool - 1, 1)
            step = per * (pool - 1) / max(model_count - 1, 1)
        except Exception:
            pass
    return duration, step


def _trajectory_series(run_dir: Path, entry: dict) -> dict:
    """frame -> {time_ns, contacts, total, closest, rmsd} from <stem>_timeseries.csv."""
    import csv

    state = entry["path"].stem
    stem = state[:-len("_frames")] if state.endswith("_frames") else state
    path = Path(run_dir) / "artifacts" / "md" / f"{stem}_timeseries.csv"
    series: dict = {}
    if not path.exists():
        return series
    try:
        with path.open() as handle:
            for row in csv.DictReader(handle):
                series[int(row["frame"])] = {
                    "time_ns": float(row.get("time_ns") or 0.0),
                    "contacts": float(row.get("contacts_4p5") or 0.0),
                    "total": float(row.get("pairs_total") or 0.0),
                    "closest": float(row.get("closest_A") or 0.0),
                    "rmsd": float(row.get("binder_rmsd_A") or 0.0),
                }
    except Exception:
        return {}
    return series


def _trajectory_hud(values: dict | None) -> str:
    """Small live-numbers panel for one trajectory frame."""
    if not values:
        return ""
    rows = [
        ("sim time", f"{values['time_ns']:.3f} ns"),
        ("contacts held", f"{values['contacts']:.0f} / {values['total']:.0f}"),
        ("closest atoms", f"{values['closest']:.2f} A"),
        ("binder RMSD", f"{values['rmsd']:.2f} A"),
    ]
    cells = "".join(f'<div class="row"><span class="k">{key}</span>'
                    f'<span class="v">{value}</span></div>' for key, value in rows)
    return f'<div class="panel" id="hud">{cells}</div>'


def _zoom_panel(pairs: int) -> str:
    """Markup for the hot-zone inset panel."""
    return ('<div class="panel" id="zoom"><div id="zoomv"></div>'
            f'<div class="zlabel"><span>hot zone \u00b7 interface residues</span>'
            f'<span><b>{pairs}</b> closest pairs</span></div></div>')


def _zoom_anchor_lines(model_text: str, highlights, margin: float = 5.0) -> str:
    """Invisible corner atoms around the interface, so the inset camera frames
    exactly the hot zone. Returns "" when the highlights carry no residues."""
    wanted = set()
    for hint in highlights:
        if hint.get("repr") == "cartoon":
            continue
        for sel in hint.get("sels") or []:
            if sel.get("chain") is not None and sel.get("resi") is not None:
                wanted.add((int(sel["resi"]), str(sel["chain"])))
    if not wanted:
        return ""
    coords = [np.array(_xyz(line)) for line in _atoms(model_text)
              if (int(line[22:26]), line[21]) in wanted]
    if not coords:
        return ""
    arr = np.array(coords)
    lo, hi = arr.min(axis=0) - margin, arr.max(axis=0) + margin
    corners = [(lo[0], lo[1], lo[2]), (lo[0], lo[1], hi[2]), (lo[0], hi[1], lo[2]),
               (hi[0], lo[1], lo[2]), (lo[0], hi[1], hi[2]), (hi[0], lo[1], hi[2]),
               (hi[0], hi[1], lo[2]), (hi[0], hi[1], hi[2])]
    lines = ["HETATM %5d %-4s %3s %1s%4d    %8.3f%8.3f%8.3f  1.00 20.00           C  "
             % (9000 + serial, "X", DUM, "Z", 1, x, y, z)
             for serial, (x, y, z) in enumerate(corners, start=1)]
    return "\n".join(lines) + "\n"


def _trajectory_contacts(run_dir: Path, entry: dict) -> list:
    """Closest interface residue pairs, from the run's stats json."""
    state = entry["path"].stem
    stem = state[:-len("_frames")] if state.endswith("_frames") else state
    path = Path(run_dir) / "artifacts" / "md" / f"{stem}_stats.json"
    out = []
    if not path.exists():
        return out
    try:
        data = json.loads(path.read_text())
        for item in data.get("top_contacts") or []:
            res_a, chain_a = str(item.get("a", "")).split(":")
            res_b, chain_b = str(item.get("b", "")).split(":")
            out.append({"a": [int(res_a), chain_a], "b": [int(res_b), chain_b],
                        "d": float(item.get("d") or 0.0)})
    except Exception:
        return []
    return out


def _trajectory_patch(run_dir: Path, entry: dict) -> list:
    """Target-side hotspot patch tokens (surface colouring), from stats json."""
    state = entry["path"].stem
    stem = state[:-len("_frames")] if state.endswith("_frames") else state
    path = Path(run_dir) / "artifacts" / "md" / f"{stem}_stats.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        patch = []
        for token in data.get("patch_tokens") or []:
            res, chain = str(token).split(":")
            patch.append([int(res), chain])
        return patch
    except Exception:
        return []


def _model_texts(text: str) -> list:
    """Split a multi-model PDB into per-model PDB texts."""
    blocks = text.split("MODEL")
    if len(blocks) <= 1:
        return [text]
    return ["MODEL" + block for block in blocks[1:]]


def _anchor_lines_all(texts: list, extra: float) -> str:
    """Invisible corner atoms over every atom of every model.

    The frames of a trajectory are superposed on the target, but the binder
    still moves. One fixed box for all frames keeps the camera steady.
    """
    coords = np.array([_xyz(line) for text in texts for line in _atoms(text)])
    lo, hi = coords.min(axis=0) - extra, coords.max(axis=0) + extra
    lines = []
    corners = [(lo[0], lo[1], lo[2]), (lo[0], lo[1], hi[2]), (lo[0], hi[1], lo[2]),
               (hi[0], lo[1], lo[2]), (lo[0], hi[1], hi[2]), (hi[0], lo[1], hi[2]),
               (hi[0], hi[1], lo[2]), (hi[0], hi[1], hi[2])]
    for serial, (x, y, z) in enumerate(corners, start=1):
        lines.append("HETATM %5d %-4s %3s %1s%4d    %8.3f%8.3f%8.3f  1.00 20.00           C  "
                     % (9000 + serial, "X", DUM, "Z", 1, x, y, z))
    return "\n".join(lines) + "\n"


def _insert_anchor(model_text: str, anchor: str) -> str:
    """Place the anchor atoms inside the model block (before ENDMDL/END)."""
    if "\nENDMDL" in model_text:
        return model_text.replace("\nENDMDL", "\n" + anchor + "ENDMDL", 1)
    if "\nEND" in model_text:
        return model_text.replace("\nEND", "\n" + anchor + "END", 1)
    return model_text + anchor


def _trajectory_pages(structure_text, entry, highlights, rows, fmt, wanted_frames,
                      style, run_dir, width, height, binder_chain=None, orbit=False):
    """Frame pages for a real MD trajectory (one model per page)."""
    models = _model_texts(structure_text)
    if len(models) < 2:
        raise SystemExit("trajectory mode needs a multi-model PDB (MODEL records)")
    if binder_chain:
        # One fixed turn for the whole movie: the binder->target axis stays
        # screen-horizontal, so the camera never drifts between frames.
        atoms0 = _atoms(models[0])
        binder_lines = [line for line in atoms0 if line[21] == binder_chain]
        target_lines = [line for line in atoms0 if line[21] != binder_chain]
        if binder_lines and target_lines:
            rotation, origin = _axis_frame(binder_lines, target_lines)
            models = [_rotate_text(text, rotation, origin) for text in models]
    picks = analyze.subsample_indices(len(models), wanted_frames)
    duration, step = _md_timing(run_dir, entry, len(models))
    series = _trajectory_series(run_dir, entry)
    surface_mode = style == "surface+cartoon"
    contacts = _trajectory_contacts(run_dir, entry) if surface_mode else []
    patch = _trajectory_patch(run_dir, entry) if surface_mode else []
    zoom_anchor = _zoom_anchor_lines(models[0], highlights) if surface_mode else ""
    anchor = _anchor_lines_all(models, 2.5)
    title = entry.get("label") or entry["path"].stem
    subtitle = (f"real all-atom molecular dynamics · {entry.get('stage', '')} stage "
                f"· run {run_dir.name}")
    pages = []
    span = max(1, len(picks) - 1)
    for position, index in enumerate(picks):
        time_line = (f"frame {index + 1} / {len(models)} · t = {index * step:.2f} ns"
                     if step else f"frame {index + 1} / {len(models)}")
        caption = _caption_html([
            ("Real molecular dynamics (OpenMM, AMBER14 force field, GBn2 implicit "
             "solvent, 300 K). Not an animation.", False),
            (time_line, False),
            ("Frames are superposed on the target chain. A short run like this is a "
             "physics test of the predicted pose. It is not a binding assay.", True),
        ])
        # a slow turntable over the clip: one full turn, so the movie loops
        angle = 360.0 * position / span if orbit else None
        zoom_structure = _insert_anchor(models[index], zoom_anchor) if zoom_anchor else None
        zoom_panel = _zoom_panel(len(contacts)) if surface_mode else ""
        config = {"highlights": highlights, "angle": angle, "bridge": None, "style": style,
                  "zoom": bool(zoom_structure), "contacts": contacts, "patch": patch}
        pages.append(_build_page(_insert_anchor(models[index], anchor), fmt, config,
                                 title, subtitle, rows, _trajectory_hud(series.get(index)),
                                 zoom_panel, caption, width, height, zoom_structure))
    return pages, {"mode": "trajectory", "models": len(models),
                   "rendered": len(picks), "style": style, "orbit": bool(orbit),
                   "zoom_inset": bool(zoom_anchor), "duration_ns": duration}


def _binder_pose_texts(complex_text: str, binder_chain: str,
                       steps: int = 32, start_offset: float = 40.0) -> list:
    """PDB texts from a far pose to the docked pose (scripted, no physics)."""
    direction = np.array([1.0, 0.0, 0.0])  # the rotated complex points +X at the binder
    poses = []
    for step in range(steps):
        progress = step / max(1, steps - 1)
        ease = 1 - (1 - progress) ** 3
        poses.append(_offset_text(complex_text, binder_chain,
                                  direction * (start_offset * (1 - ease))))
    return poses


# ------------------------------------------------------------------ movie

def start_hang_server() -> int:
    """A local server that accepts connections and never answers.

    It backs the load gate below: an image pointed at it never finishes, which
    holds the page's load event open until the gate releases it.
    """
    import socket
    import threading
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(128)
    port = srv.getsockname()[1]

    def loop() -> None:
        held = []
        while True:
            try:
                conn, _ = srv.accept()
            except OSError:
                return
            held.append(conn)  # keep it open, never respond

    threading.Thread(target=loop, daemon=True).start()
    return port


LOAD_GATE = """<img id="loadgate" src="http://127.0.0.1:{port}/hold" style="display:none">
<script>
(function() {{
  var g = document.getElementById('loadgate');
  function release() {{ g.src = 'data:image/gif;base64,R0lGODlhAQABAAAAACw='; }}
  var iv = setInterval(function() {{
    if (window.__surface_done) {{ clearInterval(iv); setTimeout(release, 900); }}
  }}, 120);
  setTimeout(function() {{ clearInterval(iv); release(); }}, 60000);
}})();
</script>
"""


def gate_surface_pages(pages: list) -> list:
    """Hold each page's load event until its molecular surface is drawn.

    Chrome screenshots a page when its load event fires; the 3Dmol surface
    computes in a web worker and would otherwise be missing from about half
    the frames (a blinking surface).  The 900 ms release delay lets the
    canvas composite before the shot.
    """
    port = start_hang_server()
    return [p.replace("</body>", LOAD_GATE.format(port=port) + "</body>")
            for p in pages]


def render_movie(run_dir, index: int = 0, out=None, frames: int = 36,
                 res: str = "1280x800", fps: int | None = None, hold: int = 8,
                 mode: str = "auto", design: str | None = None,
                 seed: int | None = None, workers: int | None = None,
                 style: str = "cartoon", orbit: bool = False) -> Path:
    """Render the movie; returns the output path."""
    run_dir = Path(run_dir)
    entries = serve_app._viewer_entries(run_dir)
    if not entries:
        raise SystemExit(f"no 3D structures inside {run_dir}")
    entry = entries[min(max(int(index), 0), len(entries) - 1)]
    if not Path(CHROME).exists():
        raise SystemExit("Google Chrome is missing — install it for the movie renderer")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg is missing on PATH — install it for the movie renderer")

    width, height = (int(part) for part in str(res).split("x"))
    structure_text = entry["path"].read_text(errors="replace")
    fmt = serve_app._format_of(entry["path"].name)
    highlights = serve_app._client_highlights([entry])[0]
    binder_chain = _binder_chain(entry)

    metrics = _load_design_metrics(run_dir)
    design_name, design_metrics = _resolve_design(metrics, entry, design)

    if style not in ("cartoon", "cloud", "cartoon+cloud", "surface", "surface+cartoon"):
        raise SystemExit(f"unknown style {style!r} (have: cartoon, cloud, cartoon+cloud, surface, surface+cartoon)")
    model_count = structure_text.count("\nMODEL ")
    use_trajectory = fmt == "pdb" and (mode == "trajectory"
                                       or (mode == "auto" and model_count >= 4))
    if mode == "trajectory" and not use_trajectory:
        raise SystemExit("trajectory mode needs a multi-model PDB (MODEL records)")
    use_sim = (not use_trajectory) and bool(design_metrics) and binder_chain is not None \
        and fmt == "pdb" and mode in ("auto", "sim")
    if mode == "sim" and not use_sim:
        raise SystemExit("sim mode needs a PDB complex with a binder chain and linkage scores")
    if mode == "dock" and (binder_chain is None or fmt != "pdb"):
        raise SystemExit("dock mode needs a PDB complex with a binder chain")
    effective = "trajectory" if use_trajectory else (
        "sim" if use_sim else
        ("dock" if (mode in ("auto", "dock") and binder_chain and fmt == "pdb") else "spin"))

    rows = _legend_rows(entry, binder_chain)
    with tempfile.TemporaryDirectory() as workdir:
        work = Path(workdir)
        shutil.copy(serve_app.STATIC_DIR / "3Dmol-min.js", work / "3Dmol-min.js")
        fonts_dir = serve_app.STATIC_DIR / "fonts"
        for font in FONT_FILES:
            if (fonts_dir / font).exists():
                shutil.copy(fonts_dir / font, work / font)

        if effective == "trajectory":
            pages, meta_stats = _trajectory_pages(
                structure_text, entry, highlights, rows, fmt, frames, style,
                run_dir, width, height, binder_chain=binder_chain, orbit=orbit)
        elif effective == "sim":
            pages, meta_stats = _sim_pages(
                structure_text, binder_chain, entry, run_dir, design_name,
                design_metrics, highlights, rows, seed, width, height)
        else:
            pages, meta_stats = _plain_pages(
                structure_text, binder_chain, entry, highlights, rows, fmt,
                frames, effective, run_dir.name, width, height, style=style)

        assert pages, "no frames to render"
        workers = workers or int(os.environ.get("PDT_MOVIE_WORKERS", "3"))
        wait_mode = "timeout" if style in ("surface", "surface+cartoon") else "virtual"
        if wait_mode == "timeout":
            pages = gate_surface_pages(pages)
        pngs = _render_pages(pages, work, width, height, workers, wait_mode=wait_mode)

        sequence = work / "frames"
        sequence.mkdir()
        counter = 0
        for png in pngs:
            shutil.copy(png, sequence / f"frame_{counter:04d}.png")
            counter += 1
        for _ in range(hold):
            shutil.copy(pngs[-1], sequence / f"frame_{counter:04d}.png")
            counter += 1

        out_path = Path(out) if out else run_dir / "movie.mp4"
        fps = fps or (18 if effective == "sim" else 12)
        subprocess.run(
            [ffmpeg, "-y", "-loglevel", "warning", "-framerate", str(fps),
             "-i", str(sequence / "frame_%04d.png"), "-c:v", "libx264",
             "-pix_fmt", "yuv420p", "-crf", "18", str(out_path)],
            check=True,
        )

    selectivity = design_metrics["selectivity"] if design_metrics else None
    if effective == "trajectory":
        honesty = [
            "Real all-atom molecular dynamics (OpenMM, AMBER14 + GBn2 implicit solvent).",
            "Frames are superposed on the target chain. Time labels are simulation time.",
            "A short run like this tests the predicted pose. It is not a binding assay.",
        ]
    else:
        if effective == "sim":
            honesty = [
                "Coarse-grained Langevin model. Not all-atom molecular dynamics.",
                "Wells are the mean-centred PROPKA pH-linkage term; the absolute "
                "affinity is not measured by this pipeline.",
                "PROPKA linkage scores rank candidates; they do not predict real affinities.",
                "Time is simulation steps, not physical seconds.",
            ]
        elif effective == "dock":
            honesty = [
                "Scripted preview: the binder slides onto its predicted contact pose.",
                "No physics runs in this clip. The physics view is --mode sim.",
            ]
        else:
            honesty = [
                "Static structure rotation of the predicted pose. No physics in this clip.",
            ]
    meta = {
        "mode": effective,
        "design": design_name,
        "selectivity_kcal": selectivity,
        "frames": len(pages),
        "fps": fps,
        "res": res,
        "seed": seed if seed is not None else sim_mod.SimParams().seed,
        "structure": entry["path"].name,
        "label": entry.get("label", ""),
        "stage": entry.get("stage", ""),
        "stats": meta_stats,
        "honesty": honesty,
    }
    meta_path = out_path.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, indent=1))
    print(f"meta: {meta_path.name} (mode {meta['mode']}, design {design_name})")
    return out_path
