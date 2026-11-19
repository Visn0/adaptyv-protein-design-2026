"""Shared 3Dmol viewer for every workbench surface.

One implementation, many surfaces: the home-page challenge cards, the
per-species target tabs and the run pages all mount the same viewer code.
Do not inline `$3Dmol.createViewer` anywhere else — call `block()` instead.

The house look lives here and only here: transparent background (or a solid
one on request), grey cartoon, one slow Y rotation unless the user prefers
reduced motion, a fade-in, and a plain error line when the file is missing.
"""

SCRIPT = "<script src='/static/3Dmol-min.js'></script>"

# window.pdt3d.mount(el, {bg, hints}) — loads 3Dmol once, then draws el.dataset.src.
LIB_JS = (
    "<script>(function () {"
    "window.pdt3d = window.pdt3d || {};"
    "function with3Dmol(fn) {"
    "  if (window.$3Dmol) { fn(); return; }"
    "  const s = document.createElement('script');"
    "  s.src = '/static/3Dmol-min.js';"
    "  s.onload = fn;"
    "  document.head.appendChild(s);"
    "}"
    "function mount(el, opts) {"
    "  if (!el || !el.dataset.src) return;"
    "  opts = opts || {};"
    "  if (el.dataset.v) { if (el._v) { el._v.resize(); el._v.render(); } return; }"
    "  el.dataset.v = '1';"
    "  with3Dmol(function () {"
    "  fetch(el.dataset.src).then(function (r) {"
    "    if (!r.ok) throw new Error(); return r.text(); })"
    "    .then(function (txt) {"
    "      el.innerHTML = '';"
    "      const v = $3Dmol.createViewer(el, { backgroundAlpha: 0 });"
    "      el._v = v;"
    "      if (opts.bg) v.setBackgroundColor(opts.bg, 1);"
    "      v.addModel(txt, txt.trimStart().startsWith('data_') ? 'cif' : 'pdb');"
    "      v.setStyle({}, { cartoon: { color: '#9aa7bc' } });"
    "      (opts.hints || []).forEach(function (h) {"
    "        h.sels.forEach(function (s) {"
    "          if (h.repr === 'cartoon') { v.setStyle(s, { cartoon: { color: h.color } }); }"
    "          else { v.setStyle(s, { stick: { color: h.color, radius: 0.15 } });"
    "                 v.setStyle(s, { sphere: { color: h.color, scale: 0.35 } }); }"
    "        });"
    "      });"
    # NOTE: LIB_JS is concatenated into ONE line, so it must never contain a
    # "//" comment (it would swallow the rest of the script - broke the target
    # viewers on 2026-10-30). Explanations live here, not in the JS.
    "      const focusSel = (opts.hints && opts.hints.length) ? opts.hints[0].sels[0] : null;"
    "      v.zoomTo(focusSel || {}, 0);"
    "      if (focusSel) v.zoom(0.78);"
    "      v.render();"
    "      if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {"
    "        setInterval(function () { v.rotate(3, 'y'); v.render(); }, 300);"
    "      }"
    "      el.classList.remove('viewer-loading');"
    "      el.classList.add('viewer-fade'); void el.offsetWidth; el.classList.add('on');"
    "    })"
    "    .catch(function () { el.classList.remove('viewer-loading');"
    "      el.textContent = 'Structure file is missing.'; });"
    "  });"
    "}"
    "window.pdt3d.mount = mount;"
    "})();</script>"
)


def block(init_js: str) -> str:
    """Return the viewer library plus one page-specific init snippet."""
    return SCRIPT + LIB_JS + "<script>" + init_js + "</script>"
