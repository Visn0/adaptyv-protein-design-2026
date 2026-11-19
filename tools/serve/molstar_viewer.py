"""The shared Mol* structure-explorer page — one template for every viewer.

Every 3D page in the workbench is built from VIEWER_PAGE: the header, the left
toolbar, the DESIGNS panel, the in-canvas legend of visible designs, the
hover/click design label, the colouring options and the caption. A caller
supplies the scene items and the labels; nothing else is duplicated.

`items` is the scene: one dict per structure, in this shape:
    {"id", "label", "color", "pdb", "chains", "chainColors",
     "interface", "on", "scores"}
The target structure is an item too (id "target").
"""
from __future__ import annotations

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[2]
ASSETS = REPO / "challenges" / "03-glp1r" / "viewers" / "assets"


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


def load_icons(assets: pathlib.Path | None = None) -> tuple[str, str]:
    """The two toolbar icons (cartoon, surface), pinned to pixels."""
    base = assets or ASSETS
    return (_normalize_icon((base / "cartoon.svg").read_text()),
            _normalize_icon((base / "surface.svg").read_text()))


VIEWER_PAGE = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
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
  #legend { position: absolute; left: 12px; top: 12px; z-index: 21; background: rgba(20, 24, 41, .85);
            border: 1px solid #1d2435; border-radius: 10px; padding: 8px 10px; max-height: 190px;
            overflow-y: auto; display: none; }
  #legend .lt { font-family: ui-monospace, Menlo, monospace; font-size: 10px; letter-spacing: .08em;
                color: #8b93a7; margin-bottom: 5px; }
  #legend .lrow { display: flex; align-items: center; font-size: 11.5px; color: #cbd2dd;
                  padding: 2px 0; font-family: ui-monospace, Menlo, monospace; }
  #legend .ldot { display: inline-block; width: 9px; height: 9px; border-radius: 3px; margin-right: 8px;
                  flex: none; }
  #hoverlabel { position: absolute; z-index: 25; background: rgba(20, 24, 41, .95);
                border: 1px solid #0da2e7; border-radius: 8px; padding: 5px 10px; font-size: 12px;
                font-family: ui-monospace, Menlo, monospace; color: #e8ebf2; display: none;
                pointer-events: none; max-width: 320px; line-height: 1.45; }
  #hoverlabel .hl { color: #8b93a7; font-size: 11px; }
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
  #head .stabs { display: flex; gap: 4px; margin-left: 2px; }
  .stab { padding: 5px 13px; border: 1px solid #2a3050; border-radius: 999px;
          background: rgba(20, 24, 41, .85); color: #8b93a7;
          font: 600 11px/1 inherit; letter-spacing: .02em; cursor: pointer; }
  .stab:hover { color: #e6e9f2; }
  .stab.cur { color: #e6e9f2; border-color: #7aa2ff; }
</style></head>
<body>
<div id="shell">
  <div id="head"><span class="t">Structure explorer</span><div id="speciesTabs" class="stabs"></div><span class="lab">__LABEL__</span></div>
  <div id="viewport">
    <div id="app"></div>
    <div id="legend"><div class="lt">Visible designs</div><div id="legend-rows"></div></div>
    <div id="hoverlabel"></div>
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

// One source of truth for the score vocabulary: the DESIGNS panel renders these
// as chips, the hover box joins them with a separator. Two formatters had already
// drifted (the hover box dropped the "agon" prefix).
function scoreParts(scores) {
  const parts = [];
  if (scores.ipsae != null) parts.push('ipSAE ' + scores.ipsae.toFixed(3));
  if (scores.iptm != null) parts.push('ipTM ' + scores.iptm.toFixed(3));
  if (scores.pdockq2 != null) parts.push('pDockQ2 ' + scores.pdockq2.toFixed(3));
  if (scores.activation) parts.push('agon ' + scores.activation);
  return parts;
}

function chipHtml(scores) {
  return scoreParts(scores)
    .map(function (p) { return '<span class="chip">' + p + '</span>'; })
    .join('');
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
    // Selection is PER DESIGN, not per structure: picking a design keeps it
    // visible on every species tab. Default: only the best three designs
    // (the generator marks their items on), the rest are one eye-click away.
    function baseDesign(item) {
      return item.design || (item.id.startsWith('c4mn_') ? item.id.slice(5) : item.id);
    }
    const sel = {};
    ITEMS.forEach(function (item) {
      if (item.id === 'target' || item.id === 'target-mouse') return;
      const b = baseDesign(item);
      sel[b] = (sel[b] === undefined) ? (item.on !== false) : (sel[b] || item.on !== false);
    });
    function refreshVis() {
      ITEMS.forEach(function (item) {
        const sp = item.species || 'human';
        const isTarget = item.id === 'target' || item.id === 'target-mouse';
        vis[item.id] = isTarget ? (sp === curSpecies) : (!!sel[baseDesign(item)] && sp === curSpecies);
      });
    }
    const rowsById = {};
    const speciesList = [...new Set(ITEMS.map(i => i.species || 'human'))];
    let curSpecies = 'human';
    refreshVis();

    function syncRows() {
      ITEMS.forEach(function (item) {
        const row = rowsById[item.id];
        if (row) row.classList.toggle('off', !vis[item.id]);
      });
    }

    const tabsBar = document.getElementById('speciesTabs');
    if (speciesList.length > 1) {
      speciesList.forEach(function (sp) {
        const b = document.createElement('button');
        b.className = 'stab' + (sp === curSpecies ? ' cur' : '');
        b.textContent = sp.charAt(0).toUpperCase() + sp.slice(1);
        b.onclick = async function () {
          curSpecies = sp;
          tabsBar.querySelectorAll('.stab').forEach(x => x.classList.remove('cur'));
          b.classList.add('cur');
          refreshVis();
          syncRows();
          await rebuild();
          updateLegend();
          frameOnDesigns(true);
        };
        tabsBar.appendChild(b);
      });
    } else {
      tabsBar.style.display = 'none';
    }

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
      // The camera is NOT reset here: toggling designs or switching themes must
      // not move the view. Framing happens on load, on the reset button and on
      // a species switch, via frameOnDesigns().
    }

    // Frame the camera on the visible designs: the generator precomputes each
    // binder's bounding sphere (item.focus), so the default view shows the
    // interaction region - the binders on their epitope - instead of the
    // whole 639-residue ectodomain with the designs lost in the middle.
    // The species tabs frame their own visible set; with nothing visible the
    // camera falls back to fitting everything.
    function frameOnDesigns(animate) {
      const spheres = ITEMS
        .filter(function (i) { return i.focus && vis[i.id] && i.id.indexOf('target') !== 0; })
        .map(function (i) { return { center: i.focus.center, radius: i.focus.radius * 1.1 }; });
      try {
        if (spheres.length) {
          // signature is focusSpheres(xs, sphereOf, options): the second argument
          // is a mapper from each item to its Sphere3D (verified in the bundle).
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
    function updateLegend() {
      const rows = document.getElementById('legend-rows');
      rows.innerHTML = '';
      ITEMS.forEach(function (item) {
        if (vis[item.id] === false) return;
        const row = document.createElement('div');
        row.className = 'lrow';
        const dot = document.createElement('span');
        dot.className = 'ldot';
        dot.style.background = hex(item.color);
        const name = document.createElement('span');
        name.textContent = item.label;
        row.appendChild(dot); row.appendChild(name);
        rows.appendChild(row);
      });
      document.getElementById('legend').style.display = rows.children.length ? 'block' : 'none';
    }
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
      if (item.scores && (item.scores.ipsae != null || item.scores.iptm != null || item.scores.pdockq2 != null)) {
        right.innerHTML = chipHtml(item.scores);
      }
      const eye = document.createElement('button');
      eye.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"></path><circle cx="12" cy="12" r="3"></circle></svg>';
      rowsById[item.id] = row;
      if (!vis[item.id]) row.classList.add('off');
      eye.onclick = async function () {
        const b = baseDesign(item);
        sel[b] = !sel[b];
        refreshVis();
        syncRows();
        await rebuild();
        updateLegend();
      };
      row.appendChild(left); row.appendChild(right); row.appendChild(eye);
      pop.appendChild(row);
    });

    // hover: name the design under the pointer
    let mx = 0, my = 0;
    const vp = document.getElementById('viewport');
    const hoverBox = document.getElementById('hoverlabel');
    // #hoverlabel is absolute inside #viewport, which sits below #head, so pointer
    // coords need the viewport origin subtracted. The rect is cached: it only moves
    // on resize or fullscreen.
    let vpRect = vp.getBoundingClientRect();
    function remeasure() { vpRect = vp.getBoundingClientRect(); }
    window.addEventListener('resize', remeasure);
    document.addEventListener('fullscreenchange', remeasure);
    vp.addEventListener('mousemove', function (e) { mx = e.clientX; my = e.clientY; });
    // Remember the camera before a click, so a click can put it back (no zoom-in).
    // Bound to #app rather than #viewport: #viewport also wraps the toolbar and the
    // legend, and a snapshot taken on a button press is only ever discarded.
    let camSnap = null;
    (document.getElementById('app') || vp).addEventListener('pointerdown', function () {
      try { camSnap = plugin.canvas3d.camera.getSnapshot(); } catch (e) {}
    });
    function labelOfLoci(loci) {
      try {
        const el = loci && loci.elements && loci.elements[0];
        if (!el || !el.unit) return null;
        const m = el.unit.model;
        return (m && m.label) || (m && m.model && m.model.label) || null;
      } catch (e) { return null; }
    }
    // What to show on hover: the design, the residue under the pointer, its scores.
    // Mol* packs loci indices either as an Interval (an IntTuple, i.e. a plain
    // number, so indices[0] is undefined) or as a SortedArray of UNIT-local
    // indices. The old indices[0] read was therefore undefined for a single picked
    // atom and the wrong index space otherwise, so no residue ever rendered.
    // getFirstLocation does the unit.elements indirection for us.
    const SE = Molstar.StructureElement;
    const SP = Molstar.StructureProperties;
    function infoOfLoci(loci) {
      const design = labelOfLoci(loci);
      if (!design) return null;
      let residue = null;
      try {
        const loc = SE.Loci.getFirstLocation(loci);
        if (loc) {
          residue = SP.atom.label_comp_id(loc) + ' ' + SP.residue.label_seq_id(loc)
            + ' · chain ' + SP.chain.label_asym_id(loc);
        }
      } catch (e) { window.__errors.push('residue: ' + e); }
      return { design: design, residue: residue };
    }
    // A click must not dim or keep a selection. plugin.behaviors.focus does not
    // exist in Mol* 4.18 (the focus manager is plugin.managers.structure.focus),
    // so the old subscription never registered and its branch here never ran;
    // both are deleted rather than left behind a guard that always fails.
    function clearFocus() {
      try {
        const ia = plugin.managers.interactivity;
        ia.lociSelects.deselectAll();
        ia.lociHighlights.clearHighlights();
      } catch (e) { window.__errors.push('clearFocus: ' + e); }
    }
    // Camera.FocusLoci animates its zoom, so the restore has to land after it.
    function restoreCamera() {
      try { if (camSnap) plugin.canvas3d.camera.setState(camSnap); }
      catch (e) { window.__errors.push('camera: ' + e); }
    }
    const BY_LABEL = new Map(ITEMS.map(function (i) { return [i.label, i]; }));
    // The box is built once. hover fires up to 30x/s, so a pointer move over the
    // same residue only repositions it instead of reparsing markup.
    const hName = document.createElement('b');
    const hResBr = document.createElement('br');
    const hRes = document.createElement('span');
    const hScBr = document.createElement('br');
    const hSc = document.createElement('span');
    hRes.className = 'hl';
    hSc.className = 'hl';
    hoverBox.replaceChildren(hName, hResBr, hRes, hScBr, hSc);
    let lastKey = null;
    function showInfo(info) {
      if (!info) { hoverBox.style.display = 'none'; return; }
      const key = info.design + '|' + (info.residue || '');
      if (key !== lastKey) {
        lastKey = key;
        const parts = scoreParts((BY_LABEL.get(info.design) || {}).scores || {});
        hName.textContent = info.design;
        hRes.textContent = info.residue || '';
        hSc.textContent = parts.join(' · ');
        hResBr.hidden = hRes.hidden = !info.residue;
        hScBr.hidden = hSc.hidden = parts.length === 0;
      }
      hoverBox.style.display = 'block';
      // measured, so the CSS max-width stays the only width constant
      const x = Math.min(mx - vpRect.left + 14, vpRect.width - hoverBox.offsetWidth - 8);
      hoverBox.style.left = Math.max(x, 8) + 'px';
      hoverBox.style.top = Math.max(my - vpRect.top - 30, 8) + 'px';
    }
    function hoverLoci(ev) {
      // Mol* behaviors emit either the loci itself or { current: { loci } }
      if (!ev) return null;
      if (ev.elements) return ev;
      const cur = ev.current;
      if (!cur) return null;
      return cur.elements ? cur : (cur.loci || null);
    }
    try {
      plugin.behaviors.interaction.hover.subscribe(function (ev) {
        showInfo(infoOfLoci(hoverLoci(ev)));
      });
      window.__hoverWired = true;
    } catch (e) { window.__errors.push('hover: ' + e); }
    try {
      plugin.behaviors.interaction.click.subscribe(function (ev) {
        showInfo(infoOfLoci(hoverLoci(ev)));
        clearFocus();
        setTimeout(restoreCamera, 0);
      });
      window.__clickWired = true;
    } catch (e) { window.__errors.push('click: ' + e); }

    await rebuild();
    updateLegend();
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


def render_viewer_page(items, title: str, label: str, slug: str,
                       binder_chain: str = "A", icons: tuple[str, str] | None = None,
                       caption: str | None = None) -> str:
    """The full HTML page for one viewer: items in, page out."""
    icon_cartoon, icon_surface = icons if icons else load_icons()
    import json

    html = (VIEWER_PAGE
            .replace("__ITEMS__", json.dumps(items))
            .replace("__TITLE__", title)
            .replace("__LABEL__", label)
            .replace("__SLUG__", slug)
            .replace("__ICON_CARTOON__", icon_cartoon)
            .replace("__ICON_SURFACE__", icon_surface)
            .replace("__BINDER__", binder_chain))
    return html
