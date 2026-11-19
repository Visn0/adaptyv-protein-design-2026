"""Build the static site for Cloudflare (see site/PLAN.md).

The export renders the app's own pages with the app's own render functions,
so the deployed pages are the same pages `pdt serve` shows. It reads
committed files only: run folders are ignored, and a local build and a CI
build produce the same files.

The steps:

1. Render the index, the challenge homes, the campaign pages, the complete
   histories, the About page and the 404 page into the dist directory.
2. Copy the shared static assets (fonts, CSS, 3Dmol) and one copy of the
   Mol* engine, shared by every explorer page.
3. Copy every viewer asset and target payload that a page references.
   Viewer assets are copied only when a page references them.
4. Inject the Cloudflare Web Analytics beacon into the top-level pages. The
   viewer iframes stay clean, so one visit stays one page view.
5. Walk every page in the dist. The export stops and lists the misses when a
   reference does not resolve.

Usage: pdt export --out site/dist
"""
from __future__ import annotations

import hashlib
import json
import posixpath
import re
import shutil
import urllib.parse
from pathlib import Path

from tools import common
from tools.experiments import runner
from tools.serve import app as serve_app
from tools.serve import brief as brief_mod

# The Cloudflare Web Analytics snippet. The token is public by design; it
# lives in site/config.json.
BEACON = (
    '<script type="module" src="https://static.cloudflareinsights.com/beacon.min.js"'
    " data-cf-beacon='{\"token\": \"%s\"}'></script>"
)

# Routes the Worker answers itself. Pages may link to them, and the dist
# holds no file for them.
WORKER_ROUTES = {"/stats", "/stats.json"}

# href / src / data-src, single or double quoted.
_REF = re.compile(r"""(?:href|src|data-src)\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)

_HEADERS = """\
# The app fetches the target payloads with JavaScript. One wildcard per rule:
# the challenge segment is a named placeholder.
/ch/*/target
  Content-Type: text/plain; charset=utf-8
/ch/:challenge/target/*
  Content-Type: text/plain; charset=utf-8
"""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


class _no_runs:
    """Make runner.status_rows return [] for the export.

    Run folders are local state. The export ignores them, so a local build
    and a CI build produce the same files.
    """

    def __enter__(self):
        self._real = runner.status_rows
        runner.status_rows = lambda *args, **kwargs: []  # noqa: ARG005

    def __exit__(self, *exc):
        runner.status_rows = self._real


def _refs(text: str) -> list[str]:
    refs = []
    for double, single in _REF.findall(text):
        ref = double or single
        if ref:
            refs.append(ref)
    return refs


def _local_ref(base_url: str, ref: str) -> str | None:
    """Turn one href/src into an absolute URL path, or None when external.

    Fragments, query strings and external targets are dropped: the checker
    looks at the path that must exist in the dist.
    """
    ref = ref.strip()
    if ref.startswith(("#", "data:", "mailto:", "tel:", "javascript:")):
        return None
    ref = ref.split("#", 1)[0].split("?", 1)[0]
    if not ref:
        return None
    if ref.startswith(("http://", "https://", "//")):
        return None
    if ref.startswith("/"):
        return posixpath.normpath(ref)
    return posixpath.normpath(posixpath.join(posixpath.dirname(base_url), ref))


class SiteExport:
    """One build of the static site into `out`."""

    def __init__(self, out: Path, beacon_token: str):
        self.out = out
        self.beacon = BEACON % beacon_token if beacon_token else ""
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.pages: list[tuple[str, Path]] = []  # (URL path, file)
        self.dedupe = False
        self.rewrites = 0
        self.copied = 0

    # ------------------------------------------------------------- writing

    def page(self, url: str, rel: str, html: str, beacon: bool = True) -> None:
        dest = self.out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if beacon and self.beacon and "</body>" in html:
            html = html.replace("</body>", self.beacon + "\n</body>", 1)
        dest.write_text(html, encoding="utf-8")
        self.pages.append((url, dest))

    def build_pages(self) -> None:
        challenges_dir = common.CHALLENGES_DIR
        self.page("/", "index.html", serve_app._herohome())
        self.page("/about", "about.html", serve_app.page_about())
        self.page("/404", "404.html", serve_app._not_found(), beacon=False)
        for challenge in list(serve_app.CHALLENGE_INFO):
            if not (challenges_dir / challenge).is_dir():
                continue
            home = serve_app.page_challenge(challenge)
            if home is None:
                self.warnings.append(f"{challenge}: no challenge page")
                continue
            self.page(f"/ch/{challenge}", f"ch/{challenge}/index.html", home)
            build = serve_app._history_build(challenge)
            if build is not None:
                back = (f"<div style='margin-bottom:28px'>"
                        f"<a href='/ch/{challenge}' style='color:#7dd3fc'>"
                        f"&larr; back to the challenge</a></div>")
                text = build.read_text(encoding="utf-8")
                if "<main>" in text:
                    text = text.replace("<main>", f"<main>{back}", 1)
                self.page(f"/ch/{challenge}/history",
                          f"ch/{challenge}/history/index.html", text)
            lineage = serve_app._load_lineage(challenge) or {}
            for exp in lineage.get("experiments", []):
                exp_id = str(exp.get("id"))
                html = serve_app.page_lineage(challenge, exp_id)
                if html is None:
                    self.warnings.append(f"{challenge}: no page for {exp_id}")
                    continue
                self.page(f"/lineage/{challenge}/{exp_id}",
                          f"lineage/{challenge}/{exp_id}/index.html", html)

    def copy_static(self) -> None:
        shutil.copytree(serve_app.STATIC_DIR, self.out / "static")

    def copy_engine(self) -> None:
        """Copy the Mol* engine once when every challenge ships the same file."""
        bundles = sorted(common.CHALLENGES_DIR.glob("*/viewers/molstar-bundle.js"))
        if not bundles:
            return
        if len({_sha256(bundle) for bundle in bundles}) == 1:
            dest = self.out / "engine" / "molstar-bundle.js"
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(bundles[0], dest)
            self.dedupe = True
            self.copied += 1
        else:
            # The copies differ, so they cannot be shared. Keep the paths the
            # pages already use.
            self.warnings.append("the molstar bundles differ; kept per-challenge copies")
            for bundle in bundles:
                challenge = bundle.relative_to(common.CHALLENGES_DIR).parts[0]
                dest = self.out / "viewer-asset" / challenge / "molstar-bundle.js"
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(bundle, dest)
                self.copied += 1

    # ------------------------------------------------------------ copying

    def _copy(self, src: Path, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        self.copied += 1

    def _target_file(self, challenge: str, rel: str | None) -> Path | None:
        if not rel:
            rel = ((brief_mod.BRIEF.get(challenge, {}).get("viewer") or {})
                   .get("file"))
        if not rel:
            return None
        root = (common.CHALLENGES_DIR / challenge).resolve()
        path = (root / rel).resolve()
        if root not in path.parents or not path.is_file():
            return None
        return path

    def _rewrite_engine(self, html: str) -> str:
        if not self.dedupe:
            return html
        for ref in ('src="../molstar-bundle.js"', 'src="molstar-bundle.js"'):
            if ref in html:
                self.rewrites += html.count(ref)
                html = html.replace(ref, 'src="/engine/molstar-bundle.js"')
        return html

    def walk_references(self) -> None:
        """Copy every viewer asset and target a page references, to closure.

        Two sets, not one: a link to another page (the sidebar links every
        sibling campaign) must not stop that page from being scanned itself.
        """
        queue = list(self.pages)
        scanned: set[str] = set()
        copied: set[str] = set()
        while queue:
            url, fs = queue.pop()
            if url in scanned:
                continue
            scanned.add(url)
            text = fs.read_text(encoding="utf-8", errors="replace")
            for ref in _refs(text):
                path = _local_ref(url, ref)
                if path is None or path in copied:
                    continue
                copied.add(path)
                new = self._handle(path)
                if new is not None:
                    queue.append(new)

    def _handle(self, path: str) -> tuple[str, Path] | None:
        """Copy the file one reference points at. Returns a page to scan next."""
        if path.startswith("/viewer-asset/"):
            parts = path[len("/viewer-asset/"):].split("/", 1)
            if len(parts) != 2:
                self.errors.append(f"bad viewer-asset path: {path}")
                return None
            challenge, rel = parts[0], urllib.parse.unquote(parts[1])
            src = common.CHALLENGES_DIR / challenge / "viewers" / rel
            if not src.is_file():
                self.errors.append(f"missing viewer asset: {path}")
                return None
            dest = self.out / path.lstrip("/")
            self._copy(src, dest)
            if dest.suffix.lower() == ".html":
                text = self._rewrite_engine(dest.read_text(encoding="utf-8"))
                dest.write_text(text, encoding="utf-8")
                return (path, dest)
            return None
        match = re.fullmatch(r"/ch/([^/]+)/target", path)
        if match:
            src = self._target_file(match.group(1), None)
            if src is None:
                self.errors.append(f"missing target payload: {path}")
                return None
            self._copy(src, self.out / path.lstrip("/"))
            return None
        match = re.fullmatch(r"/ch/([^/]+)/target/(.+)", path)
        if match:
            rel = urllib.parse.unquote(match.group(2))
            src = self._target_file(match.group(1), rel)
            if src is None:
                self.errors.append(f"missing target payload: {path}")
                return None
            self._copy(src, self.out / path.lstrip("/"))
            return None
        # Everything else must already be in the dist: pages, the engine,
        # static assets. The checker re-verifies all of them at the end.
        return None

    # ------------------------------------------------------------ checks

    def _dist_file(self, path: str) -> Path | None:
        rel = path.lstrip("/")
        if path.endswith("/"):
            candidates = [self.out / rel / "index.html"]
        else:
            candidates = [self.out / rel, self.out / (rel + ".html"),
                          self.out / rel / "index.html"]
        for cand in candidates:
            if cand.is_file():
                return cand
        return None

    def check(self) -> list[str]:
        missing = []
        for fs in sorted(self.out.rglob("*.html")):
            url = "/" + fs.relative_to(self.out).as_posix()
            text = fs.read_text(encoding="utf-8", errors="replace")
            for ref in _refs(text):
                path = _local_ref(url, ref)
                if path is None or path in WORKER_ROUTES:
                    continue
                if self._dist_file(path) is None:
                    missing.append(f"{url}: {ref}")
        return missing

    def report(self) -> None:
        files = [f for f in self.out.rglob("*") if f.is_file()]
        total = sum(f.stat().st_size for f in files)
        print(f"export: {len(files)} files, {total / 1e6:.1f} MB in {self.out}")
        for f in sorted(files, key=lambda f: f.stat().st_size, reverse=True)[:8]:
            print(f"  {f.stat().st_size / 1e6:8.2f} MB  {f.relative_to(self.out)}")
        if self.dedupe:
            print(f"export: one shared Mol* engine; {self.rewrites} reference(s) rewritten")
        for note in self.warnings:
            print(f"export: warning: {note}")
        for note in self.errors:
            print(f"export: error: {note}")


def run(out_path: Path) -> int:
    out = Path(out_path).expanduser()
    if not out.is_absolute():
        out = (Path.cwd() / out).resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    token = ""
    config = Path(common.PROJECT_ROOT) / "site" / "config.json"
    if config.is_file():
        token = (json.loads(config.read_text()).get("beacon") or {}).get("token") or ""
    if not token:
        print("export: no Web Analytics token in site/config.json; the beacon is skipped")

    export = SiteExport(out, token)
    with _no_runs():
        export.build_pages()
    export.copy_static()
    export.copy_engine()
    export.walk_references()
    (out / "_headers").write_text(_HEADERS, encoding="utf-8")
    missing = export.check()
    for item in missing:
        print(f"export: broken reference: {item}")
    export.report()
    return 2 if (missing or export.errors) else 0
