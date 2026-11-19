"""Self-contained HTML reports for experiment runs, plus the run dashboard.

A report is one HTML file: status header, per-stage summaries (key values,
tables, charts) and — when a stage provides a `viewer` hint — an inline NGL
molecule viewer with the relevant structures embedded. No network needed to
open it; the NGL bundle is inlined too.
"""
from __future__ import annotations

import html as _html
import json
import sys
from pathlib import Path

import pandas as pd

from tools import common
from tools import insights
from tools.report import charts

CONTENT_KEYS = {"stage", "tables", "charts", "viewer", "note"}

CSS = """
:root { color-scheme: dark; }
body { margin: 20px auto; max-width: 1500px; padding: 0 18px;
       background: var(--background, #0b0f14); color: var(--foreground, #e5e7eb);
       font-family: var(--app-font, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif);
       font-size: 14px; line-height: 1.5; }
h1 { font-size: 19px; margin: 4px 0 2px; }
h2 { font-size: 15px; margin: 26px 0 8px; border-bottom: 1px solid var(--border, #27272a); padding-bottom: 5px; }
.sub { color: var(--muted-foreground, #9ca3af); font-size: 12.5px; }
.badge { display: inline-block; padding: 2px 9px; border-radius: 999px; font-size: 12px; font-weight: 600; }
.badge.done { background: rgba(52, 211, 153, .18); color: #34d399; }
.badge.failed { background: rgba(248, 113, 113, .18); color: #f87171; }
.badge.running { background: rgba(96, 165, 250, .18); color: #60a5fa; }
.badge.waiting_inputs { background: rgba(245, 158, 11, .18); color: #f59e0b; }
.kv { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 4px 18px; margin: 10px 0; }
.kv div { font-size: 13px; } .kv b { color: var(--muted-foreground, #9ca3af); font-weight: 500; }
table { border-collapse: collapse; margin: 10px 0; font-size: 12.5px; width: 100%; }
th, td { border: 1px solid var(--border, #27272a); padding: 4px 8px; text-align: left; }
th { background: var(--card, #111827); color: var(--muted-foreground, #9ca3af); font-weight: 600; }
td.num { font-variant-numeric: tabular-nums; text-align: right; }
figure { margin: 12px 0; } figure svg { max-width: 100%; height: auto; }
details { margin: 12px 0; } summary { cursor: pointer; color: var(--muted-foreground, #9ca3af); }
pre { background: var(--card, #111827); padding: 10px 12px; border-radius: 8px; overflow-x: auto;
      font-size: 11.5px; line-height: 1.45; border: 1px solid var(--border, #27272a); }
.viewport { width: 100%; height: 420px; border-radius: 10px; border: 1px solid var(--border, #27272a);
            background: radial-gradient(ellipse at 50% 35%, rgba(56, 68, 89, .35), transparent 70%); }
.ngl-select { display: block; margin-top: 8px; padding: 4px 8px; border-radius: 8px; max-width: 100%;
             border: 1px solid var(--border, #27272a); background: var(--card, #111827);
             color: var(--foreground, #e5e7eb); font-size: 12.5px; }
.ngl-legend { display: flex; flex-wrap: wrap; gap: 4px 16px; margin-top: 8px; font-size: 12px;
              color: var(--muted-foreground, #9ca3af); }
.ngl-legend .sw { display: inline-block; width: 10px; height: 10px; border-radius: 3px;
                  margin-right: 6px; vertical-align: middle; }
"""


def _esc(value) -> str:
    return _html.escape(str(value))


def _cell(value) -> str:
    if isinstance(value, bool):
        return "✓" if value else "✗"
    if isinstance(value, float):
        return f"{value:,.3f}".rstrip("0").rstrip(".")
    return _esc(value)


def _kv_html(data: dict, skip: set) -> str:
    rows = []
    for key, value in data.items():
        if key in skip or value is None:
            continue
        if isinstance(value, (dict, list)):
            text = ", ".join(f"{_esc(k)}: {_esc(v)}" for k, v in value.items()) \
                if isinstance(value, dict) else ", ".join(_esc(v) for v in value[:12])
        else:
            text = _cell(value) if isinstance(value, float) else _esc(value)
        rows.append(f"<div><b>{_esc(key)}</b> {text}</div>")
    return '<div class="kv">' + "".join(rows) + "</div>" if rows else ""


def _table_html(df: pd.DataFrame, max_rows: int = 80) -> str:
    head = "".join(f"<th>{_esc(c)}</th>" for c in df.columns)
    body = []
    for _, row in df.head(max_rows).iterrows():
        cells = []
        for value in row:
            numeric = isinstance(value, (int, float)) and not isinstance(value, bool)
            cls = ' class="num"' if numeric else ""
            cells.append(f"<td{cls}>{_cell(value)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    extra = (f'<div class="sub">… {len(df) - max_rows} more rows in the CSV</div>'
             if len(df) > max_rows else "")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>{extra}"


def _read_artifact_csv(run_dir: Path, name: str) -> pd.DataFrame | None:
    path = run_dir / "artifacts" / name
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def _normalize_viewer(run_dir: Path, viewer: dict) -> dict | None:
    """Read the structure texts and attach highlights to each file.

    Accepts both schemas: a per-file `highlight` dict, and legacy global
    `highlights` entries that carry a `file` index.
    """
    global_hints = viewer.get("highlights") or []
    files = []
    for index, entry in enumerate(viewer.get("files") or []):
        path = run_dir / "artifacts" / entry["path"]
        if not path.exists():
            continue
        hints = list(entry.get("highlights") or [])
        if entry.get("highlight"):
            hints.append(entry["highlight"])
        hints.extend(hint for hint in global_hints if hint.get("file") == index)
        files.append({
            "label": entry.get("label", path.name),
            "name": path.name,
            "text": path.read_text(errors="replace"),
            "highlights": hints,
            "note": entry.get("note") or viewer.get("note", ""),
        })
    if not files:
        return None
    return {"files": files, "select": bool(viewer.get("select")), "note": viewer.get("note", "")}


_VIEWER_TEMPLATE = """
<div class="viewport" id="__STAGE_ID__"></div>
<div class="ngl-legend" id="__LEGEND_ID__"></div>
__PICKER__
<div class="sub" id="__NOTE_ID__">__NOTE__</div>
<script>__NGL__</script>
<script>
(function() {
  const data = __PAYLOAD__;
  const stageEl = document.getElementById("__STAGE_ID__");
  const noteEl = document.getElementById("__NOTE_ID__");
  const legendEl = document.getElementById("__LEGEND_ID__");
  let stage;
  try {
    stage = new NGL.Stage(stageEl, { backgroundColor: "transparent" });
  } catch (err) {
    stageEl.innerHTML = "<div class='sub' style='padding:14px'>WebGL is not available in this"
      + " window, so the 3D view cannot start here. Open the report in a normal browser, or"
      + " run <code>pdt serve</code> and use the built-in 3Dmol viewer.</div>";
    return;
  }
  stage.setParameters({ fogNear: 90, fogFar: 200 });
  window.NGL_STAGES = window.NGL_STAGES || [];
  window.NGL_STAGES.push(stage);

  function describe(hint) {
    // a legend label when the summary carries one, else a plain description
    const sels = (hint.selections || []).map(String);
    if (sels.length && sels.every(function(s) { return /^[A-Za-z0-9]$/.test(s); })) {
      return "chain " + sels.join(", ");
    }
    return sels.length + " residues (" + (hint.repr || "ball+stick") + ")";
  }
  function renderLegend(file) {
    if (!legendEl) { return; }
    legendEl.innerHTML = "";
    (file.highlights || []).forEach(function(hint) {
      const row = document.createElement("span");
      const swatch = document.createElement("span");
      swatch.className = "sw";
      swatch.style.background = hint.color || "orange";
      row.appendChild(swatch);
      row.appendChild(document.createTextNode(hint.label || describe(hint)));
      legendEl.appendChild(row);
    });
  }
  function apply(component, file) {
    component.addRepresentation("cartoon", { color: "chainindex", alpha: 0.9 });
    (file.highlights || []).forEach(function(hint) {
      component.addRepresentation(hint.repr || "ball+stick", {
        sele: hint.selections.join(" or "),
        color: hint.color || "orange",
        opacity: hint.opacity === undefined ? 0.95 : hint.opacity,
        radiusScale: 0.9
      });
    });
  }
  function mount(file, clearFirst) {
    if (clearFirst) { stage.removeAllComponents(); }
    const blob = new Blob([file.text], { type: "text/plain" });
    return stage.loadFile(blob, { ext: file.name.split(".").pop(), name: file.label })
      .then(function(component) {
        apply(component, file);
        renderLegend(file);
        if (noteEl && file.note) { noteEl.textContent = file.note; }
        if (clearFirst) { component.autoView(); }
        return component;
      });
  }

  const select = document.getElementById("__SELECT_ID__");
  if (data.select && select) {
    data.files.forEach(function(file, index) {
      const option = document.createElement("option");
      option.value = String(index);
      option.textContent = file.label;
      select.appendChild(option);
    });
    select.addEventListener("change", function() { mount(data.files[select.value], true); });
    mount(data.files[0], true);
  } else {
    data.files.forEach(function(file) { mount(file, false); });
    stage.autoView();
  }
  stage.handleResize();
  window.addEventListener("resize", function() { stage.handleResize(); });
})();
</script>"""


def _viewer_html(run_dir: Path, viewer: dict, ngl_js: str | None, index: int = 0) -> str:
    data = _normalize_viewer(run_dir, viewer)
    if not data or not ngl_js:
        return ""
    payload = json.dumps(data).replace("</", "<\\/")  # safe inside <script>
    # Unique ids per viewer: a report can hold several viewers, and duplicate
    # element ids made every script bind to the first box (blank 3D views).
    stage_id, select_id = f"ngl-stage-{index}", f"ngl-select-{index}"
    picker = (f'<select class="ngl-select" id="{select_id}" '
              'title="choose a structure"></select>' if data["select"] else "")
    return (
        _VIEWER_TEMPLATE
        .replace("__STAGE_ID__", stage_id)
        .replace("__SELECT_ID__", select_id)
        .replace("__LEGEND_ID__", f"ngl-legend-{index}")
        .replace("__NOTE_ID__", f"ngl-note-{index}")
        .replace("__PICKER__", picker)
        .replace("__NOTE__", _esc(viewer.get("note", "")))
        .replace("__NGL__", ngl_js)
        .replace("__PAYLOAD__", payload)
    )


def _stage_section(run_dir: Path, stage: dict) -> str:
    name = stage.get("stage", "stage")
    parts = [f"<h2>{_esc(name)}</h2>"]
    parts.append(_kv_html(stage, CONTENT_KEYS))
    for table_name in stage.get("tables", []) or []:
        df = _read_artifact_csv(run_dir, table_name)
        if df is None:
            continue
        parts.append(f'<div class="sub">{_esc(table_name)} — {len(df)} rows</div>')
        parts.append(_table_html(df))
    for chart in stage.get("charts", []) or []:
        df = _read_artifact_csv(run_dir, chart.get("source", ""))
        if df is None:
            continue
        svg = charts.render_chart(chart, df)
        if svg:
            parts.append(f"<figure>{svg}</figure>")
    return "".join(parts)


def render_run_report(run_dir: str | Path, out: str | Path | None = None) -> Path:
    run_dir = Path(run_dir)
    status_path = run_dir / "status.json"
    status = common.read_json(status_path) if status_path.exists() else {}
    summary = common.read_json(run_dir / "summary.json") if (run_dir / "summary.json").exists() else {}

    ngl_path = Path(__file__).parent / "assets" / "ngl.min.js"
    ngl_js = ngl_path.read_text() if ngl_path.exists() else None

    state = status.get("state", "unknown")
    parts = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        f"<title>{_esc(status.get('name', run_dir.name))} — run report</title>",
        f"<style>{CSS}</style></head><body>",
        f"<h1>{_esc(status.get('name', run_dir.name))} "
        f"<span class='badge {state}'>{_esc(state)}</span></h1>",
        f"<div class='sub'>{_esc(status.get('challenge', ''))} · pipeline "
        f"{_esc(status.get('pipeline', ''))} · started {_esc(status.get('started_utc', ''))} · "
        f"duration {_esc(status.get('duration_s', '?'))}s · git {_esc(status.get('git', '?'))} · "
        f"device {_esc((status.get('device') or {}).get('recommended', '?'))}</div>",
    ]
    try:  # link back to the hub when the report sits inside the workspace
        depth = len(run_dir.resolve().relative_to(common.PROJECT_ROOT).parts)
        parts.append(f"<div class='sub'><a href='{'../' * depth}runs-dashboard.html' "
                     "style='color:inherit'>← all experiments (dashboard)</a></div>")
    except ValueError:
        pass
    if status.get("params"):
        parts.append(_kv_html(status["params"], skip=set()))
    if status.get("error"):
        parts.append(f"<div class='sub'>error: {_esc(status['error'])}</div>")

    stages = summary.get("stages") if isinstance(summary, dict) else None
    if not stages and isinstance(summary, dict) and summary:
        stages = [dict(summary, stage="summary")]
    viewer_index = 0
    for stage in stages or []:
        parts.append(_stage_section(run_dir, stage))
        viewer = stage.get("viewer")
        if isinstance(viewer, dict) and viewer.get("files"):
            parts.append(f"<h2>{_esc(stage.get('stage', 'stage'))} — 3D view</h2>")
            parts.append(_viewer_html(run_dir, viewer, ngl_js, viewer_index))
            viewer_index += 1

    log_path = run_dir / "run.log"
    if log_path.exists():
        tail = "\n".join(log_path.read_text(errors="replace").splitlines()[-40:])
        parts.append(f"<details><summary>run.log (tail)</summary><pre>{_esc(tail)}</pre></details>")

    parts.append("</body></html>")
    out_path = Path(out) if out else run_dir / "report.html"
    out_path.write_text("".join(parts))
    return out_path


_HEADLINE_KEYS = [
    "n_designs", "best_selectivity_kcal", "sign_pass", "geometry_pass",
    "n_mutants", "improved_on_parent", "pass_all_filters",
    "n_candidates", "n_passed_hard_filters", "n_selected",
    "n_switch_conserved", "n_switch_conserved_near_groove",
    "n_sites", "max_span_A", "n_controls", "n_delta_ok", "n_sites_ok",
    "n_scored", "n_binding_at_high_pH", "best_delta_log_Ka",
    "n_backbones", "n_kept",
]


def _headline(summary) -> str:
    """Short result line for the hub: the key numbers of each stage."""
    if not isinstance(summary, dict):
        return ""
    bits = []
    for stage in (summary.get("stages") or []):
        picked = []
        for key in _HEADLINE_KEYS:
            value = stage.get(key)
            if value is None or isinstance(value, (list, dict)):
                continue
            picked.append(f"{key}={value:g}" if isinstance(value, float) else f"{key}={value}")
        if picked:
            bits.append(f"{stage.get('stage', '?')}: " + ", ".join(picked[:4]))
    return " · ".join(bits[:3])


def render_dashboard(out: str | Path | None = None, challenge: str | None = None) -> Path:
    """Clickable hub: challenge -> experiment -> run report (with the 3D view).

    Theme-aware, self-contained, no network. Links are relative, so the hub
    and the reports work from any location as long as the tree stays together.
    """
    from tools.experiments import runner
    from tools.experiments import spec as spec_mod

    rows = runner.status_rows(challenge=challenge, recent=200)
    out_path = Path(out) if out else (common.PROJECT_ROOT / "runs-dashboard.html")

    style = """
    body { margin: 0; color: var(--foreground, #d4d4d8); font-size: 13px;
           font-family: var(--app-font, -apple-system, "Segoe UI", Roboto, sans-serif); }
    h3 { margin: 16px 0 0; font-size: 13.5px; }
    table { border-collapse: collapse; margin-top: 6px; }
    th, td { padding: 3px 12px 3px 0; text-align: left; vertical-align: top; }
    th { color: var(--muted-foreground, #9ca3af); font-weight: 500; font-size: 12px; }
    td.num { font-variant-numeric: tabular-nums; }
    a { color: var(--accent, #60a5fa); text-decoration: none; }
    a:hover { text-decoration: underline; }
    .badge { display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: 11.5px; font-weight: 600; }
    .badge.done { color: #34d399; background: rgba(52,211,153,.15); }
    .badge.failed { color: #f87171; background: rgba(248,113,113,.15); }
    .badge.running { color: #60a5fa; background: rgba(96,165,250,.15); }
    .badge.waiting_inputs { color: #f59e0b; background: rgba(245,158,11,.15); }
    .sub { color: var(--muted-foreground, #9ca3af); font-size: 12px; margin-top: 6px; }
    .legend { border: 1px solid var(--border, #1d2435); border-radius: 12px; padding: 10px 14px;
              margin: 10px 0; background: var(--card, rgba(19,22,38,.6)); }
    .mleg { display: flex; gap: 10px; align-items: baseline; padding: 2px 0; flex-wrap: wrap; }
    .mleg .mono { color: var(--foreground, #d4d4d8); font-size: 12px; }
    .mleg .dir { font-size: 11px; padding: 1px 9px; border-radius: 999px;
                 border: 1px solid var(--border, #1d2435); color: var(--muted-foreground, #9ca3af); }
    .mleg .dir.higher { color: #34d399; border-color: rgba(52,211,153,.35); }
    .mleg .dir.lower { color: #60a5fa; border-color: rgba(96,165,250,.35); }
    .mleg .dir.range { color: #f59e0b; border-color: rgba(245,158,11,.35); }
    .mleg .swatch { width: 11px; height: 11px; border-radius: 3px; display: inline-block; }
    .vchip { display: inline-block; padding: 1px 9px; border-radius: 999px;
             font-size: 11.5px; font-weight: 600; }
    .vchip.promising { color: #34d399; background: rgba(52,211,153,.14); }
    .vchip.partial { color: #f59e0b; background: rgba(245,158,11,.14); }
    .vchip.insufficient { color: #cbd5e1; background: rgba(148,163,184,.14); }
    .vchip.negative { color: #f87171; background: rgba(248,113,113,.14); }
    .vchip.check { color: #a78bfa; background: rgba(167,139,250,.14); }
    .vchip.waiting { color: #f59e0b; background: rgba(245,158,11,.10); }
    .vchip.failed { color: #f87171; background: rgba(248,113,113,.16); }
    """
    groups: dict[str, list[dict]] = {}
    for row in rows:
        groups.setdefault(row.get("challenge", "?"), []).append(row)

    specs_by_challenge: dict[str, list[str]] = {}
    specs_by_name: dict[str, object] = {}
    try:
        for spec in spec_mod.discover():
            specs_by_challenge.setdefault(spec.challenge, []).append(spec.name)
            specs_by_name[spec.name] = spec
    except Exception as exc:  # the hub must render even with a broken spec
        print(f"warning: spec discovery failed for the dashboard: {exc}", file=sys.stderr)

    body = [
        "<h3 style='margin:0'>Experiment hub</h3>",
        "<div class='sub'>Click a challenge, then an experiment. Each report shows the scores, "
        "the charts, and a 3D view of the binder on the target.</div>",
        insights.colour_legend_html(),
        "<div class='legend'>"
        "<div class='mleg'><span class='mono'>reading the numbers</span>"
        "<span class='sub'>Every challenge page in the app lists each number with its "
        "direction (higher or lower is better) and the acceptance lines. The verdict chip "
        "in the table below says what a run proves.</span></div>"
        "</div>",
    ]
    jumps = " · ".join(f"<a href='#c-{_esc(ch)}'>{_esc(ch)}</a>" for ch in sorted(groups))
    if jumps:
        body.append(f"<div class='sub'>challenges: {jumps}</div>")
    for ch in sorted(groups):
        body.append(f"<h3 id='c-{_esc(ch)}'>{_esc(ch)}</h3>")
        names = sorted(specs_by_challenge.get(ch) or [])
        if names:
            body.append(f"<div class='sub'>experiments: {_esc(', '.join(names))}</div>")
        body.append("<table><tr><th>state</th><th>experiment</th><th>started</th>"
                    "<th>dur</th><th>verdict</th><th>result</th></tr>")
        labels = insights.unique_labels(groups[ch])
        for row in sorted(groups[ch], key=insights.run_sort_key, reverse=True):
            state = row.get("state", "?")
            name = row.get("name", "?")
            run_dir = row.get("run_dir")
            href = None
            if run_dir:
                target = (Path(run_dir) / "report.html").resolve()
                try:
                    href = target.relative_to(common.PROJECT_ROOT).as_posix()
                except ValueError:
                    href = target.as_posix()
            label_text = labels.get(Path(run_dir or "").name, name)
            label = (f"<a href='{_esc(href)}'>{_esc(label_text)}</a>" if href
                     else _esc(label_text))
            verdict = insights.assess_run(specs_by_name.get(str(name)), row,
                                          row.get("summary") or {})
            body.append(
                f"<tr><td><span class='badge {state}'>{state}</span></td>"
                f"<td>{label}<div class='sub mono'>{_esc(Path(run_dir or '').name)}</div></td>"
                f"<td class='num'>{_esc(insights.format_when(row.get('started_utc')))}</td>"
                f"<td class='num'>{_esc(row.get('duration_s', '-'))}s</td>"
                f"<td><div class='sub'>{_esc(verdict.get('reason', ''))}</div></td>"
                f"<td>{_esc(_headline(row.get('summary')))}</td></tr>"
            )
        body.append("</table>")
    body.append(
        f"<div class='sub'>{len(rows)} run(s) · each report also links back here · "
        f"regenerate: pdt dashboard · generated "
        f"{_esc(insights.format_when(common.utc_now()))}</div>"
        "<div class='sub'>Tip: run <b>pdt serve</b> for the clickable workbench app "
        "(real page links + built-in 3Dmol viewer).</div>"
    )
    out_path.write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>protein-design hub</title>"
        "<style>" + style + "</style></head><body>" + "".join(body) + "</body></html>"
    )
    return out_path
