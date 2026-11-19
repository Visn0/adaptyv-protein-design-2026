"""The interactive MD player page: both pH states, cartoon, cloud or surface.

One template serves two places:

    player_document  a single self-contained HTML file (3Dmol and the
                     trajectories are inlined). This is the chat deliverable.
    player_fragment  a body fragment for `pdt serve`. The structures load
                     from /api/struct/..., the 3Dmol bundle from /static/.

Controls: state buttons (one per protonation state), style buttons
(Cartoon / Cloud / Surface), play-pause, and a frame slider.
"""
from __future__ import annotations

import json
from pathlib import Path

PAGE_CSS = """
:root { color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; padding: 20px 22px 28px; background: #0b0c14; color: #f8fafc;
       font-family: -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
       font-size: 15px; line-height: 1.6;
       background-image: linear-gradient(rgba(29,36,53,.30) 1px, transparent 1px),
                         linear-gradient(90deg, rgba(29,36,53,.30) 1px, transparent 1px);
       background-size: 34px 34px; }
.wrap { max-width: 1080px; margin: 0 auto; }
.eyebrow { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 11.5px;
           letter-spacing: .08em; text-transform: uppercase; color: #8a94a6; }
h1 { font-size: 26px; font-weight: 600; letter-spacing: -.7px; margin: 6px 0 8px; }
.note { color: #c6cdd9; font-size: 13.5px; max-width: 860px; }
.toolbar { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin: 14px 0 10px; }
.toolbar .sep { width: 1px; height: 22px; background: #1d2435; margin: 0 6px; }
button { padding: 6px 14px; border-radius: 999px; border: 1px solid #1d2435;
         background: rgba(19,22,38,.9); color: #f8fafc; font-size: 13px; cursor: pointer; }
button:hover { border-color: #2a3550; }
button.on { border-color: #0da2e7; color: #0da2e7; background: rgba(13,162,231,.08); }
.viewport { width: 100%; height: 560px; border-radius: 14px; border: 1px solid #1d2435;
            background: radial-gradient(ellipse at 50% 35%, rgba(29,36,53,.55), transparent 70%); }
input[type=range] { flex: 1 1 220px; accent-color: #0da2e7; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px;
        color: #8a94a6; }
.footer { margin-top: 10px; display: grid; gap: 3px; }
"""

PLAYER_JS = r"""
(function () {
  var config = JSON.parse(document.getElementById('mdplayer-config').textContent);
  var el = document.getElementById('mdplayer-viewport');
  var slider = document.getElementById('mdplayer-slider');
  var frameLabel = document.getElementById('mdplayer-frame');
  var playBtn = document.getElementById('mdplayer-play');
  var viewer = null, frames = 0, frame = 0, timer = null, mode = 'cartoon';
  var stateIndex = 0, loading = false;

  function countModels(text) {
    var matches = text.match(/^MODEL/gm);
    return matches ? matches.length : 1;
  }
  function numFramesOf(v, text) {
    try {
      var model = v.getModel();
      if (model && typeof model.getNumFrames === 'function') {
        var n = model.getNumFrames();
        if (n) { return n; }
      }
    } catch (error) { /* fall through to the text count */ }
    return countModels(text);
  }
  function applyStyle() {
    var hints = config.hints || [];
    viewer.removeAllSurfaces();
    var paused = !timer;
    if (mode === 'cloud') {
      // point cloud: one small dot per atom; chains keep their colours
      viewer.setStyle({}, { sphere: { radius: 0.26, color: '#6b7686' } });
      hints.forEach(function (hint) {
        hint.sels.forEach(function (sel) {
          viewer.setStyle(sel, { sphere: { color: hint.color,
                                           radius: hint.repr === 'cartoon' ? 0.34 : 0.55 } });
        });
      });
      viewer.render();
      return;
    }
    viewer.setStyle({}, (mode === 'surface' && paused) ? {} : { cartoon: { colorscheme: 'chain' } });
    hints.forEach(function (hint) {
      hint.sels.forEach(function (sel) {
        if (hint.repr === 'cartoon') {
          viewer.setStyle(sel, { cartoon: { color: hint.color } });
        } else {
          viewer.setStyle(sel, { stick: { color: hint.color, radius: 0.15 } });
          viewer.setStyle(sel, { sphere: { color: hint.color, scale: 0.35 } });
        }
      });
    });
    if (mode === 'surface' && paused) {
      // surface only while paused: one surface per frame is too slow to compute while playing
      viewer.addSurface($3Dmol.SAS, { opacity: 0.75, color: '#5f6f86' }, { frame: frame });
    }
    viewer.render();
  }
  function setFrame(index) {
    frame = index;
    var result = viewer.setFrame(index);
    if (result && typeof result.then === 'function') {
      result.then(function () { viewer.render(); });
    } else {
      viewer.render();
    }
    slider.value = index;
    frameLabel.textContent = (index + 1) + ' / ' + frames;
    if (mode === 'surface' && !timer && viewer) { applyStyle(); }
  }
  function pause() {
    if (timer) { clearInterval(timer); timer = null; }
    playBtn.textContent = 'Play';
    playBtn.classList.remove('on');
    if (viewer) { applyStyle(); }
  }
  function play() {
    if (timer) { return; }
    playBtn.textContent = 'Pause';
    playBtn.classList.add('on');
    timer = setInterval(function () {
      setFrame((frame + 1) % frames);
    }, Math.max(70, Math.round(2400 / Math.max(frames, 1))));
    if (viewer) { applyStyle(); }
  }
  function loadState(index) {
    if (loading) { return; }
    loading = true;
    pause();
    stateIndex = index;
    var state = config.states[index];
    var buttonRow = document.querySelectorAll('.mdplayer-state');
    for (var n = 0; n < buttonRow.length; n++) {
      buttonRow[n].classList.toggle('on', n === index);
    }
    function show(text) {
      el.innerHTML = '';
      viewer = $3Dmol.createViewer(el, { backgroundColor: '#0b0f14' });
      viewer.addModelsAsFrames(text, 'pdb');
      frames = numFramesOf(viewer, text);
      applyStyle();
      viewer.zoomTo();
      viewer.render();
      slider.max = frames - 1;
      setFrame(0);
      var stat = document.getElementById('mdplayer-stat');
      stat.textContent = state.stat || '';
      loading = false;
      play();
    }
    if (state.pdb) {
      show(state.pdb);
    } else {
      fetch(state.url).then(function (response) { return response.text(); }).then(show);
    }
  }

  document.getElementById('mdplayer-play').addEventListener('click', function () {
    if (timer) { pause(); } else { play(); }
  });
  slider.addEventListener('input', function () {
    pause();
    setFrame(parseInt(slider.value, 10));
  });
  var styleButtons = document.querySelectorAll('.mdplayer-style');
  for (var s = 0; s < styleButtons.length; s++) {
    styleButtons[s].addEventListener('click', function (event) {
      mode = event.target.dataset.mode;
      for (var n = 0; n < styleButtons.length; n++) {
        styleButtons[n].classList.toggle('on', styleButtons[n].dataset.mode === mode);
      }
      applyStyle();
    });
  }
  var stateButtons = document.querySelectorAll('.mdplayer-state');
  for (var b = 0; b < stateButtons.length; b++) {
    stateButtons[b].addEventListener('click', function (event) {
      loadState(parseInt(event.target.dataset.index, 10));
    });
  }
  loadState(0);
})();
"""


FRAGMENT_CSS = """
#mdplayer-viewport { width: 100%; height: 560px; border-radius: 14px; border: 1px solid #1d2435;
  background: radial-gradient(ellipse at 50% 35%, rgba(29,36,53,.55), transparent 70%); }
.mdplayer-tools { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin: 14px 0 10px; }
.mdplayer-tools button { padding: 6px 14px; border-radius: 999px; border: 1px solid #1d2435;
  background: rgba(19,22,38,.9); color: #f8fafc; font-size: 13px; cursor: pointer; }
.mdplayer-tools button:hover { border-color: #2a3550; }
.mdplayer-tools button.on { border-color: #0da2e7; color: #0da2e7; background: rgba(13,162,231,.08); }
.mdplayer-tools input[type=range] { flex: 1 1 220px; accent-color: #0da2e7; }
.mdplayer-tools .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px; color: #8a94a6; }
.mdplayer-foot { margin-top: 10px; display: grid; gap: 3px; }
.mdplayer-foot .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px; color: #8a94a6; }
"""


def _toolbar_html(config: dict) -> str:
    state_buttons = "".join(
        f"<button class='mdplayer-state{' on' if index == 0 else ''}' "
        f"data-index='{index}'>{state['label']}</button>"
        for index, state in enumerate(config["states"])
    )
    return (
        "<div class='toolbar mdplayer-tools'>"
        f"{state_buttons}"
        "<span class='sep'></span>"
        "<button class='mdplayer-style on' data-mode='cartoon'>Cartoon</button>"
        "<button class='mdplayer-style' data-mode='cloud'>Cloud</button>"
        "<button class='mdplayer-style' data-mode='surface'>Surface</button>"
        "</div>"
        "<div class='toolbar mdplayer-tools'>"
        "<button id='mdplayer-play'>Pause</button>"
        "<input id='mdplayer-slider' type='range' min='0' max='0' value='0'/>"
        "<span class='mono' id='mdplayer-frame'>1 / 1</span>"
        "</div>"
    )


def _markup_html(config: dict) -> str:
    """Title, note, controls, viewport, footer and the config payload.

    The player script is NOT here. It must run after the 3Dmol bundle loads,
    so each wrapper appends it last. A missing title or note is skipped: the
    serve app prints its own page heading.
    """
    return (
        (f"<h1>{config['title']}</h1>" if config.get("title") else "")
        + (f"<div class='note'>{config['note']}</div>" if config.get("note") else "")
        + _toolbar_html(config)
        + "<div id='mdplayer-viewport' class='viewport' style='height:560px'></div>"
        + "<div class='footer mdplayer-foot'><span class='mono' id='mdplayer-stat'></span>"
        + f"<span class='mono'>{config.get('footer', '')}</span></div>"
        + "<script type='application/json' id='mdplayer-config'>"
          f"{json.dumps({'states': config['states'], 'hints': config['hints']})}"
          "</script>"
    )


def _player_script() -> str:
    return f"<script>{PLAYER_JS}</script>"


def player_fragment(config: dict, script_src: str) -> str:
    """Body fragment for the serve app: 3Dmol from a URL, states from URLs."""
    return (f"<style>{FRAGMENT_CSS}</style>"
            f"<script src='{script_src}'></script>"
            + _markup_html(config) + _player_script())


def player_document(config: dict, dmol_js_path) -> str:
    """One self-contained HTML file: CSS, 3Dmol bundle and trajectories inline."""
    dmol_js = Path(dmol_js_path).read_text(errors="replace")
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{config['title']}</title>"
        f"<style>{PAGE_CSS}</style></head><body>"
        f"<div class='wrap'><div class='eyebrow'>{config.get('eyebrow', 'Real physics · OpenMM')}</div>"
        + _markup_html(config)
        + f"</div><script>{dmol_js}</script>{_player_script()}</body></html>"
    )
