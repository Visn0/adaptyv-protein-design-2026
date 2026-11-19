"""Tiny dependency-free SVG charts (themed via the app's CSS variables).

Used by tools.report.html. All charts return inline SVG strings; colors fall
back gracefully when the page is opened outside the Hermes app.
"""
from __future__ import annotations

import html as _html

FG = "var(--foreground, #d4d4d8)"
MUTED = "var(--muted-foreground, #9ca3af)"
BORDER = "var(--border, #3f3f46)"
ACCENT = "var(--accent, #60a5fa)"
POS = "var(--success, #34d399)"
NEG = "var(--danger, #f87171)"


def _esc(text) -> str:
    return _html.escape(str(text), quote=True)


def _fmt(value) -> str:
    if isinstance(value, float):
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def hbar(pairs: list[tuple], title: str = "", note: str = "", legend: list | None = None,
         width: int = 640, row_h: int = 22, label_w: int = 220) -> str:
    """Horizontal bar chart; zero line centred so negative values read left.

    `legend` is a list of (colour, label) rows drawn under the title. When no
    legend is given and the values span both signs, a colour legend for the
    two directions is added automatically.
    """
    if not pairs:
        return ""
    values = [float(v) for _, v in pairs]
    if legend is None and min(values) < 0 < max(values):
        legend = [(NEG, "negative"), (POS, "positive")]
    shift = 18 if legend else 0
    plot_x = label_w + 8
    plot_w = width - plot_x - 70
    height = 34 + shift + row_h * len(pairs) + (30 if note else 8)
    vmax = max(abs(v) for v in values) or 1.0
    zero_x = plot_x + plot_w / 2

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="inherit">'
    ]
    if title:
        parts.append(f'<text x="4" y="16" font-size="13" fill="{FG}" font-weight="600">{_esc(title)}</text>')
    if legend:
        x = 4
        for colour, label in legend:
            parts.append(f'<rect x="{x}" y="24" width="10" height="10" rx="2" fill="{colour}" opacity="0.85"/>')
            parts.append(f'<text x="{x + 14}" y="33" font-size="11" fill="{MUTED}">{_esc(label)}</text>')
            x += 22 + 7 * len(str(label))
    parts.append(f'<line x1="{zero_x:.1f}" y1="{26 + shift}" x2="{zero_x:.1f}" y2="{height - (30 if note else 14)}" '
                 f'stroke="{BORDER}" stroke-width="1"/>')
    for i, (label, value) in enumerate(pairs):
        value = float(value)
        y = 30 + shift + i * row_h
        bar_len = abs(value) / vmax * (plot_w / 2)
        x = zero_x - bar_len if value < 0 else zero_x
        color = NEG if value < 0 else POS
        parts.append(f'<text x="{label_w}" y="{y + 11}" font-size="11" fill="{MUTED}" '
                     f'text-anchor="end">{_esc(label)}</text>')
        parts.append(f'<rect x="{x:.1f}" y="{y}" width="{max(bar_len, 1):.1f}" height="{row_h - 8}" '
                     f'rx="2" fill="{color}" opacity="0.85"><title>{_esc(label)}: {_fmt(value)}</title></rect>')
        tx = x + (bar_len + 6 if value >= 0 else -6)
        anchor = "start" if value >= 0 else "end"
        parts.append(f'<text x="{tx:.1f}" y="{y + 11}" font-size="11" fill="{FG}" '
                     f'text-anchor="{anchor}">{_fmt(value)}</text>')
    if note:
        parts.append(f'<text x="4" y="{height - 8}" font-size="11" fill="{MUTED}">{_esc(note)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def scatter(points: list[tuple], x_label: str, y_label: str, title: str = "",
            note: str = "", diagonal: bool = False, legend: list | None = None,
            width: int = 560, height: int = 400) -> str:
    """Scatter of (x, y, label) points with optional y=x reference line.

    Point colour follows the y<=x comparison: green below the line, red
    above it. A legend for the two colours is added automatically when the
    reference line is shown, unless `legend` supplies its own rows.
    """
    if not points:
        return ""
    if legend is None and diagonal:
        legend = [(POS, "below the diagonal"), (NEG, "above the diagonal")]
    pad_l, pad_r, pad_t, pad_b = 58, 16, 30, 46
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]
    lo = min(min(xs), min(ys)) if diagonal else min(xs)
    hi = max(max(xs), max(ys)) if diagonal else max(xs)

    def sx(v): return pad_l + (float(v) - lo) / (hi - lo or 1) * (width - pad_l - pad_r)
    def sy(v): return height - pad_b - (float(v) - lo) / (hi - lo or 1) * (height - pad_t - pad_b)

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
             f'viewBox="0 0 {width} {height}" font-family="inherit">']
    if title:
        parts.append(f'<text x="4" y="16" font-size="13" fill="{FG}" font-weight="600">{_esc(title)}</text>')
    # axes
    parts.append(f'<line x1="{pad_l}" y1="{height - pad_b}" x2="{width - pad_r}" y2="{height - pad_b}" '
                 f'stroke="{BORDER}"/>')
    parts.append(f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{height - pad_b}" stroke="{BORDER}"/>')
    if diagonal:
        parts.append(f'<line x1="{sx(lo):.1f}" y1="{sy(lo):.1f}" x2="{sx(hi):.1f}" y2="{sy(hi):.1f}" '
                     f'stroke="{BORDER}" stroke-dasharray="4 4"/>')
    # zero lines if in range
    if lo < 0 < hi:
        parts.append(f'<line x1="{sx(0):.1f}" y1="{pad_t}" x2="{sx(0):.1f}" y2="{height - pad_b}" '
                     f'stroke="{BORDER}" stroke-dasharray="2 4" opacity="0.6"/>')
        parts.append(f'<line x1="{pad_l}" y1="{sy(0):.1f}" x2="{width - pad_r}" y2="{sy(0):.1f}" '
                     f'stroke="{BORDER}" stroke-dasharray="2 4" opacity="0.6"/>')
    for x, y, label in points:
        color = POS if float(y) <= float(x) else NEG
        parts.append(f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="4.5" fill="{color}" opacity="0.85">'
                     f'<title>{_esc(label)}: x={_fmt(float(x))}, y={_fmt(float(y))}</title></circle>')
    # ticks (simple: ends + zero)
    for value, y in [(lo, height - pad_b), (hi, pad_t), (0.0, sy(0)) if lo < 0 < hi else (None, None)]:
        if value is None:
            continue
        parts.append(f'<text x="{pad_l - 6}" y="{y + 4:.1f}" font-size="10" fill="{MUTED}" '
                     f'text-anchor="end">{_fmt(round(float(value), 2))}</text>')
    for value in ([lo, hi] + ([0.0] if lo < 0 < hi else [])):
        parts.append(f'<text x="{sx(value):.1f}" y="{height - pad_b + 16}" font-size="10" fill="{MUTED}" '
                     f'text-anchor="middle">{_fmt(round(float(value), 2))}</text>')
    parts.append(f'<text x="{(pad_l + width - pad_r) / 2:.0f}" y="{height - 8}" font-size="11" '
                 f'fill="{MUTED}" text-anchor="middle">{_esc(x_label)}</text>')
    parts.append(f'<text x="14" y="{(pad_t + height - pad_b) / 2:.0f}" font-size="11" fill="{MUTED}" '
                 f'text-anchor="middle" transform="rotate(-90 14 {(pad_t + height - pad_b) / 2:.0f})">'
                 f'{_esc(y_label)}</text>')
    if note:
        parts.append(f'<text x="{pad_l}" y="26" font-size="11" fill="{MUTED}">{_esc(note)}</text>')
    if legend:
        right = width - pad_r
        for colour, label in reversed(legend):
            item_w = 16 + 6.2 * len(str(label))
            right -= item_w
            parts.append(f'<rect x="{right:.1f}" y="17" width="10" height="10" rx="2" '
                         f'fill="{colour}" opacity="0.85"/>')
            parts.append(f'<text x="{right + 14:.1f}" y="26" font-size="11" fill="{MUTED}">{_esc(label)}</text>')
            right -= 10
    parts.append("</svg>")
    return "".join(parts)


SERIES_COLORS = ("#60a5fa", "#e879f9", "#fbbf24", "#34d399")


def line(series: list[tuple], x_label: str = "", y_label: str = "", title: str = "",
         note: str = "", hlines: list | None = None,
         width: int = 680, height: int = 260) -> str:
    """Line chart. `series` is a list of (name, [(x, y), ...]) groups.

    `hlines` draws dashed reference levels: [(value, label), ...].
    One series is common. Two series compare the two pH states.
    """
    groups = [(name, points) for name, points in series if points]
    if not groups:
        return ""
    hlines = list(hlines or [])
    pad_l, pad_r, pad_t, pad_b = 54, 150, 30, 40
    all_x = [x for _name, points in groups for x, _y in points]
    all_y = [y for _name, points in groups for _x, y in points] + [float(h[0]) for h in hlines]
    lo_x, hi_x = float(min(all_x)), float(max(all_x))
    lo_y, hi_y = float(min(all_y)), float(max(all_y))
    span = (hi_y - lo_y) or 1.0
    lo_y -= span * 0.06
    hi_y += span * 0.06 + 1e-9

    def sx(value): return pad_l + (float(value) - lo_x) / ((hi_x - lo_x) or 1.0) * (width - pad_l - pad_r)
    def sy(value): return height - pad_b - (float(value) - lo_y) / ((hi_y - lo_y) or 1.0) * (height - pad_t - pad_b)

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
             f'viewBox="0 0 {width} {height}" font-family="inherit">']
    if title:
        parts.append(f'<text x="4" y="16" font-size="13" fill="{FG}" font-weight="600">{_esc(title)}</text>')
    parts.append(f'<line x1="{pad_l}" y1="{height - pad_b}" x2="{width - pad_r}" '
                 f'y2="{height - pad_b}" stroke="{BORDER}"/>')
    parts.append(f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{height - pad_b}" stroke="{BORDER}"/>')
    for value, label in hlines:
        y = sy(value)
        parts.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{width - pad_r}" y2="{y:.1f}" '
                     f'stroke="{BORDER}" stroke-dasharray="3 5" opacity="0.7"/>')
        if label:
            parts.append(f'<text x="{width - pad_r + 4}" y="{y + 4:.1f}" font-size="10" '
                         f'fill="{MUTED}">{_esc(label)}</text>')
    for index, (name, points) in enumerate(groups):
        color = SERIES_COLORS[index % len(SERIES_COLORS)]
        ordered = sorted(points, key=lambda point: point[0])
        polyline = " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in ordered)
        parts.append(f'<polyline points="{polyline}" fill="none" stroke="{color}" '
                     f'stroke-width="1.6" opacity="0.9"/>')
        if name:
            legend_y = pad_t + 6 + index * 18
            parts.append(f'<line x1="{width - pad_r + 8}" y1="{legend_y}" x2="{width - pad_r + 30}" '
                         f'y2="{legend_y}" stroke="{color}" stroke-width="2"/>')
            parts.append(f'<text x="{width - pad_r + 36}" y="{legend_y + 4}" font-size="11" '
                         f'fill="{FG}">{_esc(name)}</text>')
    for value, y in ((lo_y, height - pad_b), (hi_y, pad_t)):
        parts.append(f'<text x="{pad_l - 6}" y="{y + 4:.1f}" font-size="10" fill="{MUTED}" '
                     f'text-anchor="end">{_fmt(round(value, 2))}</text>')
    for value in (lo_x, hi_x):
        parts.append(f'<text x="{sx(value):.1f}" y="{height - pad_b + 16}" font-size="10" '
                     f'fill="{MUTED}" text-anchor="middle">{_fmt(round(value, 2))}</text>')
    parts.append(f'<text x="{(pad_l + width - pad_r) / 2:.0f}" y="{height - 8}" font-size="11" '
                 f'fill="{MUTED}" text-anchor="middle">{_esc(x_label)}</text>')
    parts.append(f'<text x="14" y="{(pad_t + height - pad_b) / 2:.0f}" font-size="11" '
                 f'fill="{MUTED}" text-anchor="middle" '
                 f'transform="rotate(-90 14 {(pad_t + height - pad_b) / 2:.0f})">{_esc(y_label)}</text>')
    if note:
        parts.append(f'<text x="{pad_l}" y="26" font-size="11" fill="{MUTED}">{_esc(note)}</text>')
    parts.append("</svg>")
    return "".join(parts)


def render_chart(spec: dict, table: "pandas.DataFrame") -> str:  # noqa: F821
    """Render one chart hint from a stage summary against its source table."""
    kind = spec.get("kind")
    source = spec.get("source")
    legend = spec.get("legend")
    # The retired Tamarind comparison: old runs recorded it in their specs and
    # tables; the local GPU is the only path now, so it is never rendered.
    title = str(spec.get("title", ""))
    series_col0 = spec.get("series")
    if series_col0 and series_col0 in table.columns:
        table = table[~table[series_col0].astype(str)
                      .str.contains("Tamarind", case=False, na=False)]
    if "Tamarind" in title:
        title = title.replace(" vs Tamarind", "").replace("vs Tamarind", "")
        title = title.replace("Tamarind", "").strip().rstrip(",")
    if kind == "hbar":
        value_col = spec.get("value")
        label_col = spec.get("label")
        if value_col not in table.columns:
            return ""
        pairs = list(zip(table[label_col].astype(str), table[value_col]))
        return hbar(pairs, title=title, note=spec.get("note", ""),
                    legend=legend)
    if kind == "scatter":
        x_col, y_col, label_col = spec.get("x"), spec.get("y"), spec.get("label")
        for col in (x_col, y_col):
            if col not in table.columns:
                return ""
        import pandas as pd

        frame = table[[x_col, y_col, label_col]].apply(pd.to_numeric, errors="coerce")
        frame[label_col] = table[label_col].astype(str)
        frame = frame.dropna(subset=[x_col, y_col])
        points = [(row[x_col], row[y_col], row[label_col]) for _, row in frame.iterrows()]
        return scatter(points, x_label=str(x_col), y_label=str(y_col),
                       title=title, note=spec.get("note", ""),
                       diagonal=bool(spec.get("diagonal")), legend=legend)
    if kind == "line":
        x_col, y_col = spec.get("x"), spec.get("y")
        if x_col not in table.columns or y_col not in table.columns:
            return ""
        import pandas as pd

        frame = table.copy()
        frame[x_col] = pd.to_numeric(frame[x_col], errors="coerce")
        frame[y_col] = pd.to_numeric(frame[y_col], errors="coerce")
        frame = frame.dropna(subset=[x_col, y_col])
        series_col = spec.get("series")
        groups = []
        if series_col and series_col in frame.columns:
            for name, group in frame.groupby(series_col, sort=True):
                groups.append((str(name), list(zip(group[x_col], group[y_col]))))
        else:
            groups.append((spec.get("label") or str(y_col),
                           list(zip(frame[x_col], frame[y_col]))))
        hlines = []
        for entry in (spec.get("hlines") or []):
            if isinstance(entry, dict):
                hlines.append((float(entry.get("y")), str(entry.get("label", ""))))
            elif isinstance(entry, (list, tuple)):
                hlines.append((float(entry[0]), str(entry[1]) if len(entry) > 1 else ""))
            else:
                hlines.append((float(entry), ""))
        return line(groups, x_label=str(x_col), y_label=str(y_col),
                    title=title, note=spec.get("note", ""),
                    hlines=hlines)
    return ""
