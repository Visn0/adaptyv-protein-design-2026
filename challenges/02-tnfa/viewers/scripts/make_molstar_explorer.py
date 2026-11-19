#!/usr/bin/env python
"""Build a Mol*-based structure explorer that replicates proteinbase's UI.

proteinbase's explorer runs Mol* (the PDBe/RCSB viewer) with a compact custom
UI: header, left toolbar (cartoon / surface / chains / coloring), a right icon
strip, and an expand button. This generator reproduces that UI with the same
engine, icons, colours and behaviours, for our designs.

The same page serves headless captures: load it with ``?shot=1&mode=X&view=N``
and it hides the UI, applies the mode and points the camera at one of three
viewpoints (used by ``tools/report/molstar_views.py``).

    .venv/bin/python make_molstar_explorer.py d7x-t3-3 b2x-d12-2 e1b-d7x-t3-3-v6
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

def _repo_root() -> pathlib.Path:
    """The repo root: the nearest parent that holds both tools/ and challenges/."""
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / "tools").is_dir() and (parent / "challenges").is_dir():
            return parent
    raise SystemExit("repo root not found; keep this file inside the repository")


REPO = _repo_root()
OUT = REPO / "challenges" / "02-tnfa" / "viewers"
ASSETS = Path.home() / "c2-work" / "md-anim" / "molstar"
RUNS = Path.home() / "c2-work" / "md-anim" / "runs"
FOLDS = Path.home() / "c2-work" / "genie3" / "folds"

# fold CIF per design (the best-scoring Boltz-2 sample of each run)
FOLD_CIFS = {
    "d7x-t3-3": FOLDS / "d7x-t3-3" / "boltz_results_d7x-t3-3" / "predictions" / "d7x-t3-3" / "d7x-t3-3_model_0.cif",
    "b2x-d12-2": FOLDS / "b2x-d12-2" / "boltz_results_b2x-d12-2" / "predictions" / "b2x-d12-2" / "b2x-d12-2_model_2.cif",
    "e1b-d7x-t3-3-v6": FOLDS / "e1b-d7x-t3-3-v6" / "boltz_results_e1b-d7x-t3-3-v6" / "predictions" / "e1b-d7x-t3-3-v6" / "e1b-d7x-t3-3-v6_model_2.cif",
}

# proteinbase's own icon assets, fetched from their public site
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

PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>__TITLE__ \u00b7 structure explorer</title>
<style>
  html, body { margin: 0; background: #0b0c14; width: 100vw; height: 100vh; overflow: hidden;
               font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif; color: #e8ebf2; }
  #shell { position: absolute; inset: 0; display: flex; flex-direction: column; }
  #head { display: flex; align-items: center; justify-content: space-between; gap: 16px;
          border-bottom: 1px solid #1d2435; padding: 16px 24px; font-size: 12px; flex: none; }
  #head .t { font-weight: 500; }
  #head a { font-family: ui-monospace, 'SF Mono', Menlo, monospace; color: #0da2e7;
            text-decoration: none; }
  #head a:hover { text-decoration: underline; text-underline-offset: 4px; }
  #viewport { position: relative; flex: 1; min-height: 0; }
  #app { position: absolute; inset: 0; }
  /* keep only the canvas from Mol*'s own chrome */
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
  #chains { position: absolute; left: 12px; bottom: 12px; z-index: 22; }
  #chains .pill { background: rgba(20, 24, 41, .85); border: 1px solid #1d2435; border-radius: 8px;
                  color: #b0b8d1; font-size: 11px; letter-spacing: .08em; padding: 7px 12px;
                  cursor: pointer; font-family: ui-monospace, Menlo, monospace; }
  #chains .pop { display: none; position: absolute; bottom: 42px; left: 0; background: rgba(20, 24, 41, .95);
                 border: 1px solid #1d2435; border-radius: 10px; padding: 8px; min-width: 170px; }
  #chains.open .pop { display: block; }
  #chains .row { display: flex; align-items: center; justify-content: space-between; gap: 12px;
                 padding: 6px 8px; border-radius: 6px; font-size: 12px; color: #cbd2dd; }
  #chains .row:hover { background: rgba(255, 255, 255, .06); }
  #chains .row button { background: none; border: none; cursor: pointer; padding: 2px; display: flex; }
  #chains .row button svg { color: #b0b8d1; }
  #chains .row.off { opacity: .45; }
  #chains .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 7px; }
  #colormodal { display: none; position: absolute; inset: 0; z-index: 30; align-items: center;
                justify-content: center; background: rgba(6, 8, 14, .55); }
  #colormodal.open { display: flex; }
  #colormodal .box { background: #141829; border: 1px solid #1d2435; border-radius: 14px;
                     padding: 22px 24px; width: min(640px, 86%); }
  #colormodal .bhead { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
  #colormodal .bhead .t { font-size: 16px; font-weight: 600; }
  #colormodal .bhead button { background: none; border: none; cursor: pointer; color: #b0b8d1; display: flex; }
  #colormodal .cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
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
  <div id="head"><span class="t">Structure explorer</span><a id="pdblink" href="#" title="local fold \u2014 no public PDB entry">__PDBLABEL__</a></div>
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
      <button class="ibtn" id="b-chains" aria-label="Chain visibility" title="Chain visibility">
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
      <button class="ibtn" id="b-shot" title="Screenshot / State Snapshot">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" style="color:#b0b8d1">
          <path d="M14.25 2.26l-.08-.04-.01.02C13.46 2.09 12.74 2 12 2 6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10c0-4.75-3.31-8.72-7.75-9.74zM19.41 9h-7.99l2.71-4.7c2.4.66 4.35 2.42 5.28 4.7zM13.1 4.08L10.27 9l-1.15 2L6.4 6.3C7.84 4.88 9.82 4 12 4c.37 0 .74.03 1.1.08zM5.7 7.09L8.54 12l1.15 2H4.26C4.1 13.36 4 12.69 4 12c0-1.85.64-3.55 1.7-4.91zM4.59 15h7.98l-2.71 4.7c-2.4-.67-4.34-2.42-5.27-4.7zm6.31 4.91L14.89 13l2.72 4.7C16.16 19.12 14.18 20 12 20c-.38 0-.74-.04-1.1-.09zm7.4-3l-4-6.91h5.43c.17.64.27 1.31.27 2 0 1.85-.64 3.55-1.7 4.91z"></path></svg></button>
      <button class="ibtn" id="b-select" title="Toggle Selection Mode">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" style="color:#b0b8d1">
          <path d="M10.07,14.27C10.57,14.03 11.16,14.25 11.4,14.75L13.7,19.74L15.5,18.89L13.19,13.91C12.95,13.41 13.17,12.81 13.67,12.58L13.95,12.5L16.25,12.05L8,5.12V15.9L9.82,14.43L10.07,14.27M13.64,21.97C13.14,22.21 12.54,22 12.31,21.5L10.13,16.76L7.62,18.78C7.45,18.92 7.24,19 7,19A1,1 0 0,1 6,18V3A1,1 0 0,1 7,2C7.24,2 7.47,2.09 7.64,2.23L7.65,2.22L19.14,11.86C19.57,12.22 19.62,12.85 19.27,13.27C19.12,13.45 18.91,13.57 18.7,13.61L15.54,14.23L17.74,18.96C18,19.46 17.76,20.05 17.26,20.28L13.64,21.97Z"></path></svg></button>
    </div>
    <div id="chains">
      <button class="pill" id="chains-toggle">CHAINS</button>
      <div class="pop" id="chains-pop"></div>
    </div>
    <div id="colormodal">
      <div class="box">
        <div class="bhead"><span class="t">Coloring Options</span>
          <button id="colormodal-close" aria-label="Close">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
                 stroke-linecap="round"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg></button></div>
        <div class="cards">
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
    <div id="caption">__CAPTION__</div>
  </div>
</div>
<script>
// Headless capture: Mol* requests a WebGL context with failIfMajorPerformanceCaveat,
// which software renderers (SwiftShader) refuse. Relax it for shot mode.
(function () {
  if (!new URLSearchParams(location.search).get('shot')) return;
  const original = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function (type, attrs) {
    if (type && String(type).indexOf('webgl') === 0) {
      attrs = Object.assign({}, attrs || {}, { failIfMajorPerformanceCaveat: false });
    }
    return original.call(this, type, attrs);
  };
})();
</script>
<script src="molstar-bundle.js"></script>
<script>
window.__errors = [];
window.onerror = function (msg, src, line) { window.__errors.push(String(msg) + ' @' + line); };
const STRUCTURE = __STRUCTURE__;
const INTERFACE = __INTERFACE__;   // [[resi, chain], ...]
const DESIGN = __DESIGN__;
const COLORS = __COLORS__;         // per-chain uniform colours
const BINDER_CHAINS = __BINDER_CHAINS__;

(async function () {
  try {
    const spec = Molstar.DefaultPluginUISpec();
    spec.layout = { initial: { isExpanded: false } };
    spec.canvas3d = { renderer: { backgroundColor: 0x0b0c14 },
                      camera: { helper: { axes: { name: 'off' } } } };
    const plugin = await Molstar.createPluginUI({
      target: document.getElementById('app'),
      spec: spec,
      render: Molstar.renderReact18,
    });
    window.__molstar = plugin;
    await plugin.clear();
    const data = await plugin.builders.data.rawData({ data: STRUCTURE, label: DESIGN });
    const trajectory = await plugin.builders.structure.parseTrajectory(data, 'pdb');
    await plugin.builders.structure.hierarchy.applyPreset(trajectory, 'default');
    window.__loaded = true;

    const MS = Molstar.MolScriptBuilder;
    const B = plugin.builders.structure.representation;
    const structures = () => plugin.managers.structure.hierarchy.current.structures;
    const structureRef = () => structures()[0];

    let mode = 'cartoon';
    let theme = 'chain';        // chain | plddt | hydrophobicity | interface
    const visible = {};
    Object.keys(COLORS).forEach(ch => { visible[ch] = true; });

    function chainExpr(ch) {
      return MS.struct.generator.atomGroups({
        'chain-test': MS.core.rel.eq([MS.ammp('label_asym_id'), ch]) });
    }
    function interfaceExpr(ch) {
      const resis = [...new Set(INTERFACE.filter(pair => pair[1] === ch).map(pair => pair[0]))];
      if (!resis.length) return null;
      const tests = resis.map(r => MS.core.rel.eq([MS.ammp('auth_seq_id'), r]));
      return MS.struct.generator.atomGroups({
        'chain-test': MS.core.rel.eq([MS.ammp('label_asym_id'), ch]),
        'residue-test': tests.length === 1 ? tests[0] : MS.core.logic.or(tests),
      });
    }
    function colourProps(ch) {
      if (theme === 'plddt') {
        // 'uncertainty' = the confidence theme. Its palette reads colours[0] at the HIGH
        // end, so the ramp is reversed: deep blue for high pLDDT down to red for low.
        return { color: 'uncertainty',
                 colorParams: { domain: [0, 100],
                                list: { kind: 'interpolate',
                                        colors: [0x0053D6, 0x65CBF3, 0xFFDB13, 0xFF7D45] } } };
      }
      if (theme === 'hydrophobicity') { return { color: 'hydrophobicity', colorParams: {} }; }
      return { color: 'uniform', colorParams: { value: COLORS[ch] } };
    }

    async function rebuild() {
      await plugin.managers.structure.component.clearComponents([structureRef()]);
      for (const ch of Object.keys(COLORS)) {
        if (!visible[ch]) continue;
        const cell = await plugin.builders.structure.tryCreateComponentFromExpression(
          structureRef().cell, chainExpr(ch), 'chain-' + ch, { label: 'Chain ' + ch });
        if (!cell) continue;
        const props = mode === 'surface'
          ? { type: 'molecular-surface', typeParams: { quality: 'medium' } }
          : { type: 'cartoon', typeParams: {} };
        Object.assign(props, colourProps(ch), { size: 'uniform', sizeParams: { value: 1 } });
        await B.addRepresentation(cell, props);
      }
      if (theme === 'interface') {
        for (const ch of Object.keys(COLORS)) {
          if (!visible[ch]) continue;
          const expr = interfaceExpr(ch);
          if (!expr) continue;
          const cell = await plugin.builders.structure.tryCreateComponentFromExpression(
            structureRef().cell, expr, 'interface-' + ch, { label: 'Interface ' + ch });
          if (cell) {
            await B.addRepresentation(cell, {
              type: 'ball-and-stick', typeParams: { sizeFactor: 0.16 },
              color: 'uniform', colorParams: { value: 0xfbbf24 },
              size: 'uniform', sizeParams: { value: 1 } });
          }
        }
      }
    }

    function setActive(id, on) { document.getElementById(id).classList.toggle('active', !!on); }

    document.getElementById('b-cartoon').onclick = async function () {
      mode = 'cartoon'; setActive('b-cartoon', true); setActive('b-surface', false);
      await rebuild();
    };
    document.getElementById('b-surface').onclick = async function () {
      mode = 'surface'; setActive('b-surface', true); setActive('b-cartoon', false);
      await rebuild();
    };

    const chainsBox = document.getElementById('chains');
    document.getElementById('b-chains').onclick = function () {
      chainsBox.classList.toggle('open');
    };

    const colorModal = document.getElementById('colormodal');
    document.getElementById('b-color').onclick = function () { colorModal.classList.add('open'); };
    document.getElementById('colormodal-close').onclick = function () { colorModal.classList.remove('open'); };
    document.querySelectorAll('#colormodal .card').forEach(function (card) {
      card.onclick = async function () {
        const pick = card.dataset.theme;
        document.querySelectorAll('#colormodal .card').forEach(c => c.classList.remove('active'));
        card.classList.add('active');
        theme = pick;
        colorModal.classList.remove('open');
        await rebuild();
      };
    });

    // a click outside (or Escape) closes the open panel / dialog
    document.addEventListener('click', function (e) {
      if (!chainsBox.contains(e.target)
          && !document.getElementById('b-chains').contains(e.target)) {
        chainsBox.classList.remove('open');
      }
    });
    colorModal.addEventListener('click', function (e) {
      if (e.target === colorModal) colorModal.classList.remove('open');
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        colorModal.classList.remove('open');
        chainsBox.classList.remove('open');
      }
    });

    document.getElementById('b-reset').onclick = function () {
      if (plugin.managers.camera && plugin.managers.camera.reset) plugin.managers.camera.reset();
    };
    document.getElementById('b-shot').onclick = function () {
      const canvas = document.querySelector('#app canvas');
      if (!canvas) return;
      canvas.toBlob(function (blob) {
        if (!blob) return;
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = DESIGN + '_explorer.png';
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

    // chain visibility list
    const pop = document.getElementById('chains-pop');
    for (const ch of Object.keys(COLORS)) {
      const row = document.createElement('div');
      row.className = 'row';
      const dot = document.createElement('span');
      dot.className = 'dot';
      dot.style.background = '#' + COLORS[ch].toString(16).padStart(6, '0');
      const name = document.createElement('span');
      name.textContent = BINDER_CHAINS.indexOf(ch) >= 0
        ? 'Chain ' + ch + ' (binder)' : 'Chain ' + ch + ' (target)';
      const left = document.createElement('span');
      left.appendChild(dot); left.appendChild(name);
      const eye = document.createElement('button');
      eye.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"></path><circle cx="12" cy="12" r="3"></circle></svg>';
      eye.onclick = async function () {
        visible[ch] = !visible[ch];
        row.classList.toggle('off', !visible[ch]);
        await rebuild();
      };
      row.appendChild(left); row.appendChild(eye);
      pop.appendChild(row);
    }

    await rebuild();
    plugin.managers.camera.reset();

    // headless shot mode: ?shot=1&mode=<cartoon|surface|plddt|hydrophobicity|interface>&view=<0..2>
    const q = new URLSearchParams(location.search);
    if (q.get('shot')) {
      document.getElementById('head').style.display = 'none';
      document.getElementById('expand').style.display = 'none';
      document.getElementById('chains').style.display = 'none';
      document.getElementById('caption').style.display = 'none';
      document.querySelectorAll('.float').forEach(e => { e.style.display = 'none'; });
      const m = q.get('mode') || 'cartoon';
      if (m === 'plddt' || m === 'hydrophobicity' || m === 'interface') { theme = m; }
      else { mode = m; }
      const v = parseInt(q.get('view') || '0', 10);
      await rebuild();
      plugin.managers.camera.reset();
      await new Promise(r => setTimeout(r, 700));
      const c = plugin.canvas3d.camera;
      const T = c.target, P = c.position;
      const R = Math.hypot(P[0] - T[0], P[1] - T[1], P[2] - T[2]);
      const el = 15 * Math.PI / 180, th = v * 2 * Math.PI / 3;
      const dir = [Math.sin(th) * Math.cos(el), Math.sin(el), Math.cos(th) * Math.cos(el)];
      plugin.managers.camera.setSnapshot({
        position: [T[0] + dir[0] * R, T[1] + dir[1] * R, T[2] + dir[2] * R],
        target: T, up: [0, 1, 0] });
      window.__shotReady = m + ':' + v;
      document.title = 'SHOT_READY ' + m + ' ' + v;
    }
    window.__ready = true;
  } catch (err) {
    window.__errors.push('bootstrap: ' + err);
    window.__ready = 'error';
  }
})();
</script></body></html>
"""


def compute_interface(structure, binder_chains, cutoff: float = 4.5) -> list:
    """Interface residue pairs (resi, chain) between binder and target.

    Heavy-atom contacts within ``cutoff`` angstrom, both sides of the interface.
    """
    import numpy as np

    binder, target = [], []
    for chain in structure.get_chains():
        cid = chain.id.strip()
        bucket = binder if cid in binder_chains else target
        for residue in chain.get_residues():
            for atom in residue.get_atoms():
                if atom.element != "H":
                    bucket.append((atom.coord, residue.id[1], cid))
    tokens = set()
    if binder and target:
        b = np.array([entry[0] for entry in binder])
        t = np.array([entry[0] for entry in target])
        for i in range(0, len(b), 500):
            chunk = b[i:i + 500]
            d2 = ((chunk[:, None, :] - t[None, :, :]) ** 2).sum(-1)
            for bi, ti in np.argwhere(d2 <= cutoff ** 2):
                tokens.add((binder[i + bi][1], binder[i + bi][2]))
                tokens.add((target[ti][1], target[ti][2]))
    return sorted(tokens)


def fold_pdb(design: str) -> str:
    """The Boltz fold as PDB text with pLDDT in the B-factor column."""
    import io

    from Bio.PDB import MMCIFParser, PDBIO

    structure = MMCIFParser(QUIET=True).get_structure("m", str(FOLD_CIFS[design]))
    handle = io.StringIO()
    writer = PDBIO()
    writer.set_structure(structure[0])
    writer.save(handle)
    return handle.getvalue()


def interface_tokens(design: str) -> list:
    """Interface residue pairs (resi, chain): MD stats when present, else the fold."""
    stats_path = RUNS / design / "artifacts" / "md" / f"{design}_stats.json"
    if stats_path.exists():
        stats = json.loads(stats_path.read_text())
        tokens = set()
        for pair in stats.get("top_contacts", []) or []:
            for key in ("a", "b"):
                token = pair.get(key)
                if token:
                    resi, chain = str(token).split(":")
                    tokens.add((int(resi), chain))
        for token in stats.get("patch_tokens", []) or []:
            resi, chain = str(token).split(":")
            tokens.add((int(resi), chain))
        if tokens:
            return sorted(tokens)
    # no MD run for this design: derive the interface from the fold itself
    import io

    from Bio.PDB import PDBParser

    handle = io.StringIO(fold_pdb(design))
    structure = PDBParser(QUIET=True).get_structure("m", handle)
    return compute_interface(structure[0], binder_chains={"A"})


def build_page(structure: str, interface: list, colors: dict, design: str,
               caption: str, binder_chains: list, pdblabel: str) -> str:
    """The explorer/shot page as a string (pure function)."""
    return (PAGE
            .replace("__TITLE__", design)
            .replace("__PDBLABEL__", pdblabel)
            .replace("__ICON_CARTOON__", ICON_CARTOON.replace("<svg", "<svg class=\"icon\"", 1))
            .replace("__ICON_SURFACE__", ICON_SURFACE.replace("<svg", "<svg class=\"icon\"", 1))
            .replace("__STRUCTURE__", json.dumps(structure))
            .replace("__INTERFACE__", json.dumps(interface))
            .replace("__COLORS__", json.dumps(colors))
            .replace("__BINDER_CHAINS__", json.dumps(binder_chains))
            .replace("__DESIGN__", json.dumps(design))
            .replace("__CAPTION__", caption))


def build(design: str) -> Path:
    structure = fold_pdb(design)
    chains = sorted({line[21] for line in structure.splitlines() if line.startswith("ATOM")})
    # binder pink; target chains in proteinbase's cyan family (#0099ff / #00d2ff / #03ffff)
    palette = [0xE879F9, 0x0099FF, 0x00D2FF, 0x03FFFF]
    colors = {ch: palette[i % len(palette)] for i, ch in enumerate(chains)}
    page = build_page(
        structure=structure,
        interface=interface_tokens(design),
        colors=colors,
        design=design,
        caption=(f"{design} \u00b7 Boltz-2 fold of the complex \u00b7 "
                 "a fold is a model, not a binding measurement"),
        binder_chains=["A"],
        pdblabel=f"Boltz-2 fold \u00b7 {design} \u2197",
    )
    OUT.mkdir(parents=True, exist_ok=True)
    shutil.copy(ASSETS / "molstar-bundle.js", OUT / "molstar-bundle.js")
    path = OUT / f"{design}_explorer.html"
    path.write_text(page)
    print(f"{path} ({len(page) // 1024} KB, {len(interface_tokens(design))} interface residues, "
          f"chains {chains})")
    return path


if __name__ == "__main__":
    designs = sys.argv[1:] or ["d7x-t3-3", "b2x-d12-2", "e1b-d7x-t3-3-v6"]
    for name in designs:
        build(name)
