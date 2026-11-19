#!/usr/bin/env python3
"""Build the multi-protein structure explorer: the shared TNF target plus every
designed binder of an experiment, in the same UI as the single-design explorer
(make_molstar_explorer.py) — header, left toolbar, DESIGNS panel, coloring
options — with one addition: the DESIGNS panel selects one or many designs
(colour dot + name + score chips), so they are compared against the same
target in one scene.

    .venv/bin/python make_molstar_multiview.py genie3-campaign

Reads the experiment's `viewer` design list from lineage.json, picks each
design's best at-site model, extracts the binder chain, computes its interface
residues, and embeds everything in a self-contained page.
"""
from __future__ import annotations

import csv
import io
import json
import pathlib
import re
import sys

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
CH = REPO / "challenges" / "02-tnfa"
ASSETS = pathlib.Path.home() / "c2-work" / "md-anim" / "molstar"
FOLDS = pathlib.Path.home() / "c2-work" / "genie3" / "folds"
OUT = CH / "viewers" / "multiview"

# binder palette: the standing binder pink first, then distinct hues; the
# target chains keep the cyan family (per-chain uniform)
BINDER_COLORS = [0xe879f9, 0x34d399, 0xfbbf24, 0x60a5fa, 0xf472b6, 0x22d3ee,
                 0xa78bfa, 0xfb7185, 0x4ade80, 0xfacc15]
TARGET_CHAIN_COLORS = {"B": 0x0099ff, "C": 0x00d2ff, "D": 0x03ffff}
BINDER_CHAIN = "A"

def _normalize_icon(svg: str, size: int = 22) -> str:
    """The Inkscape icons carry physical units (mm/pt) and no class; pin them
    to pixels and give them the class the toolbar CSS targets."""
    end = svg.index(">", svg.index("<svg"))
    head = svg[:end]
    head = re.sub(r'width="[^"]*"', f'width="{size}"', head, count=1)
    head = re.sub(r'height="[^"]*"', f'height="{size}"', head, count=1)
    if "class=" not in head:
        head += ' class="icon"'
    return head + svg[end:]


ICON_CARTOON = _normalize_icon((ASSETS / "cartoon.svg").read_text())
ICON_SURFACE = _normalize_icon((ASSETS / "surface.svg").read_text())

from Bio.PDB import MMCIFParser, PDBIO, Select  # noqa: E402


class _Chains(Select):
    def __init__(self, chains):
        self.chains = set(chains)

    def accept_chain(self, chain):
        return chain.id in self.chains


def best_model(design: str) -> int:
    """Best at-site sample index from the fold-row archive; 0 as fallback."""
    best = None
    for r in csv.reader(open(CH / "notes" / "genie3" / "genie3-all-scores.csv")):
        if r[0].strip() != design or r[5].strip() != "True":
            continue
        ip = float(r[2])
        if best is None or ip > best[0]:
            best = (ip, int(r[1]))
    return best[1] if best else 0


def cif_path(design: str, model: int) -> pathlib.Path:
    return (FOLDS / design / f"boltz_results_{design}" / "predictions" / design
            / f"{design}_model_{model}.cif")


def _pdb_text(structure, select=None) -> str:
    writer = PDBIO()
    writer.set_structure(structure)
    handle = io.StringIO()
    writer.save(handle, select)
    return handle.getvalue()


def design_parts(design: str):
    """(binder PDB text, interface residue numbers on the binder)."""
    model = best_model(design)
    structure = MMCIFParser(QUIET=True).get_structure("m", str(cif_path(design, model)))[0]
    binder = structure[BINDER_CHAIN]
    targets = [c for c in structure if c.id != BINDER_CHAIN]
    batoms = [(a.get_coord(), a.get_parent().id[1]) for a in binder.get_atoms()]
    contacts = set()
    for ch in targets:
        for ta in ch.get_atoms():
            tc = ta.get_coord()
            for bc, resnum in batoms:
                if ((bc[0] - tc[0]) ** 2 + (bc[1] - tc[1]) ** 2
                        + (bc[2] - tc[2]) ** 2) <= 4.5 ** 2:
                    contacts.add(resnum)
                    break
    binder_pdb = _pdb_text(structure, _Chains([BINDER_CHAIN]))
    return binder_pdb, sorted(contacts)


def target_pdb(design: str) -> str:
    """Chains B/C/D of the first design = the shared target."""
    model = best_model(design)
    structure = MMCIFParser(QUIET=True).get_structure("m", str(cif_path(design, model)))[0]
    return _pdb_text(structure, _Chains([c.id for c in structure if c.id != BINDER_CHAIN]))


PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>__TITLE__ \u00b7 structure explorer</title>
<style>
  html, body { margin: 0; background: #0b0c14; width: 100vw; height: 100vh; overflow: hidden;
               font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif; color: #e8ebf2; }
  #shell { position: absolute; inset: 0; display: flex; flex-direction: column; }
  #head { display: flex; align-items: center; justify-content: space-between; gap: 16px;
          border-bottom: 1px solid #1d2435; padding: 14px 22px; font-size: 12px; flex: none; }
  #head .t { font-weight: 500; }
  #head .lab { font-family: ui-monospace, 'SF Mono', Menlo, monospace; color: #0da2e7; }
  #viewport { position: relative; flex: 1; min-height: 0; }
  #app { position: absolute; inset: 0; }
  #app .msp-log, #app .msp-help, #app .msp-layout-bottom, #app .msp-sequence,
  #app .msp-viewport-controls, #app .msp-viewport-top-left-controls,
  #app .msp-animation-viewport-controls, #app .msp-left-panel-controls,
  #app .msp-state-actions, #app .msp-timeline { display: none !important; }
  .float { position: absolute; background: rgba(20, 24, 41, .85); border-radius: 10px;
           padding: 6px; display: flex; flex-direction: column; gap: 4px; z-index: 20; }
  #leftbar { left: 12px; top: 50%; transform: translateY(-50%); }
  #rightbar { right: 12px; top: 50%; transform: translateY(-50%); }
  .ibtn { background: transparent; border: none; border-radius: 8px; padding: 8px; cursor: pointer;
          display: flex; align-items: center; justify-content: center; transition: background .15s, color .15s; }
  .ibtn:hover { background: rgba(255, 255, 255, .08); }
  .ibtn.active { background: #0da2e7; }
  .ibtn svg.icon { width: 22px; height: 22px; display: block; filter: brightness(0) invert(0.7); }
  .ibtn.active svg.icon { filter: brightness(0) invert(1); }
  .ibtn svg { display: block; color: #b0b8d1; max-width: 24px; max-height: 24px; }
  #expand { position: absolute; top: 16px; right: 16px; z-index: 21; background: rgba(20, 24, 41, .85);
            border: none; border-radius: 8px; padding: 8px; cursor: pointer; display: flex;
            align-items: center; justify-content: center; transition: background .15s; }
  #expand:hover { background: rgba(35, 41, 66, .95); }
  #proteins { position: absolute; left: 12px; bottom: 12px; z-index: 22; }
  #proteins .pill { background: rgba(20, 24, 41, .85); border: 1px solid #1d2435; border-radius: 8px;
                    color: #b0b8d1; font-size: 11px; letter-spacing: .08em; padding: 7px 12px;
                    cursor: pointer; font-family: ui-monospace, Menlo, monospace; }
  #proteins .pop { display: none; position: absolute; bottom: 42px; left: 0; background: rgba(20, 24, 41, .97);
                   border: 1px solid #1d2435; border-radius: 10px; padding: 8px; min-width: 310px;
                   max-height: 55vh; overflow-y: auto; }
  #proteins.open .pop { display: block; }
  #proteins .row { display: flex; align-items: center; justify-content: space-between; gap: 12px;
                   padding: 6px 8px; border-radius: 6px; font-size: 12px; color: #cbd2dd; }
  #proteins .row:hover { background: rgba(255, 255, 255, .06); }
  #proteins .row button { background: none; border: none; cursor: pointer; padding: 2px; display: flex; }
  #proteins .row button svg { color: #b0b8d1; }
  #proteins .row.off { opacity: .45; }
  #proteins .dot { display: inline-block; width: 9px; height: 9px; border-radius: 3px; margin-right: 8px; }
  #proteins .nm { font-family: ui-monospace, Menlo, monospace; font-size: 11.5px; }
  #proteins .chip { display: inline-block; background: #141829; border: 1px solid #232c44; border-radius: 6px;
                    padding: 0 5px; font-size: 10px; color: #cfd7e6; margin-right: 4px; }
  #colormodal { display: none; position: absolute; inset: 0; z-index: 30; align-items: center;
                justify-content: center; background: rgba(6, 8, 14, .55); }
  #colormodal.open { display: flex; }
  #colormodal .box { background: #141829; border: 1px solid #1d2435; border-radius: 14px;
                     padding: 22px 24px; width: min(640px, 86%); }
  #colormodal .bhead { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
  #colormodal .bhead .t { font-size: 16px; font-weight: 600; }
  #colormodal .bhead button { background: none; border: none; cursor: pointer; color: #b0b8d1; display: flex; }
  #colormodal .cards { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
  #colormodal .card { background: #1b2035; border: 1px solid #232a44; border-radius: 10px; padding: 16px 14px;
                      cursor: pointer; text-align: center; transition: border-color .15s, background .15s; }
  #colormodal .card:hover { border-color: #0da2e7; }
  #colormodal .card.active { border-color: #0da2e7; background: rgba(13, 162, 231, .1); }
  #colormodal .card .ic { color: #b0b8d1; margin-bottom: 10px; display: flex; justify-content: center; }
  #colormodal .card .n { font-size: 13.5px; font-weight: 600; margin-bottom: 5px; }
  #colormodal .card .d { font-size: 11px; color: #8b93a7; line-height: 1.35; }
  #caption { position: absolute; left: 16px; right: 16px; bottom: 10px; text-align: center;
             font-size: 10.5px; color: #6b7386; z-index: 5; pointer-events: none; }
</style></head>
<body>
<div id="shell">
  <div id="head"><span class="t">Structure explorer</span><span class="lab">__LABEL__</span></div>
  <div id="viewport">
    <div id="app"></div>
    <button id="expand" aria-label="Enter fullscreen" title="Enter fullscreen">
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none"
           stroke="#b0b8d1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M15 3h6v6"></path><path d="m21 3-7 7"></path><path d="m3 21 7-7"></path><path d="M9 21H3v-6"></path>
      </svg></button>
    <div class="float" id="leftbar">
      <button class="ibtn active" id="b-cartoon" aria-label="Cartoon" title="Cartoon">__ICON_CARTOON__</button>
      <button class="ibtn" id="b-surface" aria-label="Surface" title="Surface">__ICON_SURFACE__</button>
      <button class="ibtn" id="b-proteins" aria-label="Designs" title="Designs">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round">
          <path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"></path>
          <circle cx="12" cy="12" r="3"></circle></svg></button>
      <button class="ibtn" id="b-color" aria-label="Residue color" title="Residue color">
        <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 384 512" height="22" width="22">
          <path d="M162.4 6c-1.5-3.6-5-6-8.9-6l-19 0c-3.9 0-7.5 2.4-8.9 6L104.9 57.7c-3.2 8-14.6 8-17.8 0L66.4 6c-1.5-3.6-5-6-8.9-6L48 0C21.5 0 0 21.5 0 48L0 224l0 22.4L0 256l9.6 0 364.8 0 9.6 0 0-9.6 0-22.4 0-176c0-26.5-21.5-48-48-48L230.5 0c-3.9 0-7.5 2.4-8.9 6L200.9 57.7c-3.2 8-14.6 8-17.8 0L162.4 6zM0 288l0 32c0 35.3 28.7 64 64 64l64 0 0 64c0 35.3 28.7 64 64 64s64-28.7 64-64l0-64 64 0c35.3 0 64-28.7 64-64l0-32L0 288zM192 432a16 16 0 1 1 0 32 16 16 0 1 1 0-32z"></path>
        </svg></button>
    </div>
    <div class="float" id="rightbar">
      <button class="ibtn" id="b-reset" title="Reset Zoom">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" style="color:#b0b8d1">
          <path d="M12 6v3l4-4-4-4v3c-4.42 0-8 3.58-8 8 0 1.57.46 3.03 1.24 4.26L6.7 14.8c-.45-.83-.7-1.79-.7-2.8 0-3.31 2.69-6 6-6zm6.76 1.74L17.3 9.2c.44.84.7 1.79.7 2.8 0 3.31-2.69 6-6 6v-3l-4 4 4 4v-3c4.42 0 8-3.58 8-8 0-1.57-.46-3.03-1.24-4.26z"></path></svg></button>
      <button class="ibtn" id="b-shot" title="Screenshot">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" style="color:#b0b8d1">
          <path d="M14.25 2.26l-.08-.04-.01.02C13.46 2.09 12.74 2 12 2 6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10c0-4.75-3.31-8.72-7.75-9.74zM19.41 9h-7.99l2.71-4.7c2.4.66 4.35 2.42 5.28 4.7zM13.1 4.08L10.27 9l-1.15 2L6.4 6.3C7.84 4.88 9.82 4 12 4c.37 0 .74.03 1.1.08zM5.7 7.09L8.54 12l1.15 2H4.26C4.1 13.36 4 12.69 4 12c0-1.85.64-3.55 1.7-4.91zM4.59 15h7.98l-2.71 4.7c-2.4-.67-4.34-2.42-5.27-4.7zm6.31 4.91L14.89 13l2.72 4.7C16.16 19.12 14.18 20 12 20c-.38 0-.74-.04-1.1-.09zm7.4-3l-4-6.91h5.43c.17.64.27 1.31.27 2 0 1.85-.64 3.55-1.7 4.91z"></path></svg></button>
      <button class="ibtn" id="b-select" title="Toggle Selection Mode">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" style="color:#b0b8d1">
          <path d="M10.07,14.27C10.57,14.03 11.16,14.25 11.4,14.75L13.7,19.74L15.5,18.89L13.19,13.91C12.95,13.41 13.17,12.81 13.67,12.58L13.95,12.5L16.25,12.05L8,5.12V15.9L9.82,14.43L10.07,14.27M13.64,21.97C13.14,22.21 12.54,22 12.31,21.5L10.13,16.76L7.62,18.78C7.45,18.92 7.24,19 7,19A1,1 0 0,1 6,18V3A1,1 0 0,1 7,2C7.24,2 7.47,2.09 7.64,2.23L7.65,2.22L19.14,11.86C19.57,12.22 19.62,12.85 19.27,13.27C19.12,13.45 18.91,13.57 18.7,13.61L15.54,14.23L17.74,18.96C18,19.46 17.76,20.05 17.26,20.28L13.64,21.97Z"></path></svg></button>
    </div>
    <div id="proteins">
      <div class="pop" id="proteins-pop"></div>
    </div>
    <div id="colormodal">
      <div class="box">
        <div class="bhead"><span class="t">Coloring Options</span>
          <button id="colormodal-close" aria-label="Close">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                 stroke-linecap="round"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg></button></div>
        <div class="cards">
          <div class="card" data-theme="chain">
            <div class="ic"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="1.7" stroke-linecap="round"><circle cx="6" cy="6" r="3"></circle>
                 <circle cx="18" cy="6" r="3"></circle><circle cx="6" cy="18" r="3"></circle>
                 <circle cx="18" cy="18" r="3"></circle></svg></div>
            <div class="n">Default</div><div class="d">Design colours — one colour per protein</div></div>
          <div class="card" data-theme="plddt">
            <div class="ic"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="1.7" stroke-linecap="round"><circle cx="7" cy="7" r="2.6"></circle>
                 <circle cx="17" cy="7" r="2.6"></circle><circle cx="12" cy="17" r="2.6"></circle>
                 <path d="M9 8.5 11 15M15 8.5 13 15M9.5 7h5"></path></svg></div>
            <div class="n">pLDDT</div><div class="d">Confidence coloring from structure prediction model</div></div>
          <div class="card" data-theme="hydrophobicity">
            <div class="ic"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 9a7 7 0 1 1-14 0z"></path>
                 <path d="M12 13v5"></path></svg></div>
            <div class="n">Hydrophobicity</div><div class="d">Color by residue hydrophobicity</div></div>
          <div class="card" data-theme="interface">
            <div class="ic"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="1.7"><rect x="4" y="4" width="12" height="12" rx="2"></rect>
                 <rect x="8" y="8" width="12" height="12" rx="2"></rect></svg></div>
            <div class="n">Interface</div><div class="d">Highlight interface residues in orange</div></div>
        </div>
      </div>
    </div>
    <div id="caption">Drag to rotate &middot; scroll to zoom &middot; designs: the eye icon on the left toolbar</div>
  </div>
</div>
<script src="../molstar-bundle.js"></script>
<script>
window.__errors = [];
window.onerror = function (msg, src, line) { window.__errors.push(String(msg) + ' @' + line); };
const ITEMS = __ITEMS__;

function chipHtml(scores) {
  let out = '';
  if (scores.human != null) out += '<span class="chip">human ' + scores.human.toFixed(3) + '</span>';
  if (scores.mouse != null) out += '<span class="chip">mouse ' + scores.mouse.toFixed(3) + '</span>';
  if (scores.ph != null) out += '<span class="chip">switch ' + (scores.ph > 0 ? '+' : '') + scores.ph.toFixed(3) + '</span>';
  return out;
}
const hex = v => '#' + v.toString(16).padStart(6, '0');

(async function () {
  try {
    const spec = Molstar.DefaultPluginUISpec();
    spec.layout = { initial: { isExpanded: false } };
    spec.canvas3d = { renderer: { backgroundColor: 0x0b0c14 },
                      camera: { helper: { axes: { name: 'off' } } } };
    const plugin = await Molstar.createPluginUI({
      target: document.getElementById('app'), spec: spec, render: Molstar.renderReact18 });
    window.__molstar = plugin;

    const MS = Molstar.MolScriptBuilder;
    const B = plugin.builders.structure.representation;
    const structures = () => plugin.managers.structure.hierarchy.current.structures;

    let mode = 'cartoon';       // cartoon | surface
    let theme = 'chain';        // chain | plddt | hydrophobicity | interface
    const vis = {};
    ITEMS.forEach(item => { vis[item.id] = item.on !== false; });

    function chainExpr(ch) {
      return MS.struct.generator.atomGroups({
        'chain-test': MS.core.rel.eq([MS.ammp('label_asym_id'), ch]) });
    }
    function interfaceExpr(item) {
      if (!item.interface.length) return null;
      const tests = item.interface.map(r => MS.core.rel.eq([MS.ammp('auth_seq_id'), r]));
      return MS.struct.generator.atomGroups({
        'chain-test': MS.core.rel.eq([MS.ammp('label_asym_id'), '__BINDER__']),
        'residue-test': tests.length === 1 ? tests[0] : MS.core.logic.or(tests) });
    }
    function colourProps(ch, fallback) {
      if (theme === 'plddt') {
        return { color: 'uncertainty',
                 colorParams: { domain: [0, 100],
                                list: { kind: 'interpolate',
                                        colors: [0x0053D6, 0x65CBF3, 0xFFDB13, 0xFF7D45] } } };
      }
      if (theme === 'hydrophobicity') { return { color: 'hydrophobicity', colorParams: {} }; }
      return { color: 'uniform', colorParams: { value: fallback } };
    }

    async function rebuild() {
      await plugin.clear();
      const shown = ITEMS.filter(i => vis[i.id]);
      for (const item of shown) {
        const data = await plugin.builders.data.rawData({ data: item.pdb, label: item.label });
        const traj = await plugin.builders.structure.parseTrajectory(data, 'pdb');
        await plugin.builders.structure.hierarchy.applyPreset(traj, 'default');
        // pair the ref with the item immediately: never trust list order
        const refs = structures();
        const ref = refs[refs.length - 1];
        if (!ref) continue;
        await plugin.managers.structure.component.clearComponents([ref]);
        for (const ch of item.chains) {
          const cell = await plugin.builders.structure.tryCreateComponentFromExpression(
            ref.cell, chainExpr(ch), 'chain-' + ch, { label: 'Chain ' + ch });
          if (!cell) continue;
          const props = mode === 'surface'
            ? { type: 'molecular-surface', typeParams: { quality: 'medium' } }
            : { type: 'cartoon', typeParams: {} };
          Object.assign(props, colourProps(ch, item.chainColors[ch]),
                        { size: 'uniform', sizeParams: { value: 1 } });
          await B.addRepresentation(cell, props);
        }
        if (theme === 'interface') {
          const expr = interfaceExpr(item);
          if (expr) {
            const cell = await plugin.builders.structure.tryCreateComponentFromExpression(
              ref.cell, expr, 'iface-' + item.id, { label: 'Interface' });
            if (cell) {
              await B.addRepresentation(cell, {
                type: 'ball-and-stick', typeParams: { sizeFactor: 0.16 },
                color: 'uniform', colorParams: { value: 0xfbbf24 },
                size: 'uniform', sizeParams: { value: 1 } });
            }
          }
        }
      }
      if (plugin.handleResize) plugin.handleResize();
    }

    // Frame the camera on the visible designs (item.focus spheres), so the
    // default view shows the interaction region, not the whole receptor.
    function frameOnDesigns(animate) {
      const spheres = ITEMS
        .filter(function (i) { return i.focus && vis[i.id] && i.id.indexOf('target') !== 0; })
        .map(function (i) { return { center: i.focus.center, radius: i.focus.radius * 1.1 }; });
      try {
        if (spheres.length) {
          plugin.managers.camera.focusSpheres(spheres, function (s) { return s; },
                                              { durationMs: animate ? 300 : 0 });
        } else if (plugin.managers.camera && plugin.managers.camera.reset) {
          plugin.managers.camera.reset();
        }
      } catch (e) { window.__errors.push('frame: ' + e); }
    }

    function setActive(id, on) { document.getElementById(id).classList.toggle('active', !!on); }

    document.getElementById('b-cartoon').onclick = async function () {
      mode = 'cartoon'; setActive('b-cartoon', true); setActive('b-surface', false); await rebuild();
    };
    document.getElementById('b-surface').onclick = async function () {
      mode = 'surface'; setActive('b-surface', true); setActive('b-cartoon', false); await rebuild();
    };

    const pbox = document.getElementById('proteins');
    document.getElementById('b-proteins').onclick = function () { pbox.classList.toggle('open'); };

    const colorModal = document.getElementById('colormodal');
    document.getElementById('b-color').onclick = function () {
      document.querySelectorAll('#colormodal .card').forEach(
        c => c.classList.toggle('active', c.dataset.theme === theme));
      colorModal.classList.add('open');
    };
    document.getElementById('colormodal-close').onclick = function () { colorModal.classList.remove('open'); };
    document.querySelectorAll('#colormodal .card').forEach(function (card) {
      card.onclick = async function () {
        document.querySelectorAll('#colormodal .card').forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        theme = card.dataset.theme;
        colorModal.classList.remove('open');
        await rebuild();
      };
    });

    // a click outside (or Escape) closes the open panel / dialog
    document.addEventListener('click', function (e) {
      if (!pbox.contains(e.target)
          && !document.getElementById('b-proteins').contains(e.target)) {
        pbox.classList.remove('open');
      }
    });
    colorModal.addEventListener('click', function (e) {
      if (e.target === colorModal) colorModal.classList.remove('open');
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        colorModal.classList.remove('open');
        pbox.classList.remove('open');
      }
    });

    document.getElementById('b-reset').onclick = function () { frameOnDesigns(true); };
    document.getElementById('b-shot').onclick = function () {
      const canvas = document.querySelector('#app canvas');
      if (!canvas) return;
      canvas.toBlob(function (blob) {
        if (!blob) return;
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = '__SLUG___explorer.png';
        a.click();
      });
    };
    let selecting = false;
    document.getElementById('b-select').onclick = function () {
      selecting = !selecting;
      this.classList.toggle('active', selecting);
      if (plugin.managers.interactivity && plugin.managers.interactivity.setProps) {
        plugin.managers.interactivity.setProps({ mode: selecting ? 'select' : 'default' });
      }
    };
    document.getElementById('expand').onclick = function () {
      if (document.fullscreenElement) { document.exitFullscreen(); }
      else { document.documentElement.requestFullscreen(); }
    };

    // designs panel: colour dot + name + scores, eye toggles one or many
    const pop = document.getElementById('proteins-pop');
    ITEMS.forEach(function (item) {
      const row = document.createElement('div');
      row.className = 'row';
      const dot = document.createElement('span');
      dot.className = 'dot';
      dot.style.background = hex(item.color);
      const name = document.createElement('span');
      name.className = 'nm';
      name.textContent = item.label;
      const left = document.createElement('span');
      left.appendChild(dot); left.appendChild(name);
      const right = document.createElement('span');
      if (item.scores && (item.scores.human != null || item.scores.mouse != null || item.scores.ph != null)) {
        right.innerHTML = chipHtml(item.scores);
      }
      const eye = document.createElement('button');
      eye.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"></path><circle cx="12" cy="12" r="3"></circle></svg>';
      if (!vis[item.id]) row.classList.add('off');
      eye.onclick = async function () {
        vis[item.id] = !vis[item.id];
        row.classList.toggle('off', !vis[item.id]);
        await rebuild();
      };
      row.appendChild(left); row.appendChild(right); row.appendChild(eye);
      pop.appendChild(row);
    });

    await rebuild();
    frameOnDesigns(false);
    window.__loaded = true;
  } catch (err) {
    window.__errors.push(String(err));
    document.getElementById('app').textContent = 'Viewer failed: ' + err;
  }
})();
</script>
</body></html>
"""


def focus_of(pdb_text, chains):
    """The binder atoms' bounding sphere, for the viewer's default camera."""
    pts = []
    for line in pdb_text.splitlines():
        if line.startswith(("ATOM", "HETATM")):
            if chains and line[21] not in chains:
                continue
            try:
                pts.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
            except ValueError:
                continue
    if not pts:
        return None
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    cz = sum(p[2] for p in pts) / len(pts)
    r = max(((p[0]-cx)**2 + (p[1]-cy)**2 + (p[2]-cz)**2) ** 0.5 for p in pts)
    return {"center": [round(cx, 1), round(cy, 1), round(cz, 1)], "radius": round(r + 6.0, 1)}


def build(exp_id: str) -> pathlib.Path | None:
    data = json.loads((CH / "lineage.json").read_text())
    exp = None
    for candidate in data.get("experiments", []):
        if candidate.get("id") == exp_id:
            exp = candidate
            break
        for chapter in candidate.get("chapters", []):
            if chapter.get("id") == exp_id and chapter.get("viewer"):
                exp = {"id": exp_id, "title": chapter["title"],
                       "summary": chapter.get("text", ""),
                       "proteins": candidate.get("proteins", []),
                       "viewer": chapter["viewer"]}
    if exp is None or not exp.get("viewer"):
        return None

    by_design = {p["design"]: p for p in exp.get("proteins", [])}
    items = [{
        "id": "target", "label": "TNF-\u03b1 trimer (target)",
        "color": TARGET_CHAIN_COLORS["B"],
        "pdb": target_pdb(exp["viewer"][0]),
        "chains": ["B", "C", "D"],
        "chainColors": dict(TARGET_CHAIN_COLORS),
        "interface": [], "scores": {},
    }]
    for index, design in enumerate(exp["viewer"]):
        binder, interface = design_parts(design)
        entry = by_design.get(design, {})
        items.append({
            "id": design, "label": design,
            "color": BINDER_COLORS[index % len(BINDER_COLORS)],
            "pdb": binder, "chains": [BINDER_CHAIN],
            "chainColors": {BINDER_CHAIN: BINDER_COLORS[index % len(BINDER_COLORS)]},
            "interface": interface,
            "focus": focus_of(binder, [BINDER_CHAIN]),
            # best three only, by the ranked viewer order (2026-10-30: the old
            # "small sets show whole" rule left several pages opening with 0-2
            # designs visible)
            "on": index < 3,
            "scores": {"human": entry.get("human"), "mouse": entry.get("mouse"),
                       "ph": entry.get("ph")},
        })
        print(f"  {design}: {len(interface)} interface residues")

    OUT.mkdir(parents=True, exist_ok=True)
    html = (PAGE
            .replace("__ITEMS__", json.dumps(items))
            .replace("__TITLE__", exp["title"])
            .replace("__LABEL__", exp["title"])
            .replace("__SLUG__", exp_id)
            .replace("__ICON_CARTOON__", ICON_CARTOON)
            .replace("__ICON_SURFACE__", ICON_SURFACE)
            .replace("__BINDER__", BINDER_CHAIN))
    out = OUT / f"{exp_id}.html"
    out.write_text(html)
    return out


if __name__ == "__main__":
    for exp_id in sys.argv[1:]:
        path = build(exp_id)
        print(f"{exp_id} -> {path}" if path else f"{exp_id}: nothing to build")
