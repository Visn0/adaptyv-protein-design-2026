"""pdt — command line for the protein-design workspace.

    pdt exp list                 list experiments
    pdt exp run --all -j 4       run everything, four at a time
    pdt exp run c2-fold-w1-gpu   run one by name
    pdt exp status               recent runs
    pdt report <run_dir>         (re)build one run's HTML report
    pdt dashboard                hub HTML: challenge -> experiment -> 3D view
    pdt serve                    local web app (hub, reports, 3Dmol viewer)
    pdt export --out site/dist   static site build for the Cloudflare Worker
    pdt movie <run_dir>          MP4 of one structure (real MD playback, sim, dock, spin)
    pdt device                   show cpu / mps / cuda availability
    pdt fetch-data               copy the public target files into challenges/*/inputs
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from tools import common
from tools.experiments import devices
from tools.experiments import runner
from tools.experiments import spec as spec_mod
from tools.report import html as report_html


def cmd_exp_list(args) -> int:
    specs = spec_mod.discover()
    if args.challenge:
        specs = [s for s in specs if s.challenge == args.challenge]
    if not specs:
        print("no experiments found")
        return 1
    for spec in specs:
        stages = ",".join(spec.stages) or "all"
        flags = " [network]" if spec.requires_network else ""
        print(f"{spec.challenge:<9} {spec.name:<32} pipeline={spec.pipeline:<3} "
              f"stages={stages:<26}{flags}")
        if spec.description:
            print(f"          {spec.description}")
    return 0


def cmd_exp_run(args) -> int:
    all_specs = spec_mod.discover()
    selected = []
    wanted = set(args.names)
    if args.all or not wanted:
        selected = [s for s in all_specs if not args.challenge or s.challenge == args.challenge]
    else:
        missing = wanted - {s.name for s in all_specs}
        if missing:
            print(f"unknown experiment name(s): {sorted(missing)} — see `pdt exp list`")
            return 2
        selected = [s for s in all_specs if s.name in wanted]
    results = runner.run_specs(selected, jobs=max(1, args.jobs), dry_run=args.dry_run)
    if results:
        hub = report_html.render_dashboard(challenge=args.challenge)
        print(f"\nhub: open {hub} in a browser (click: challenge -> experiment -> 3D view)")
    return 0 if all(r.get("state") in ("done", "waiting_inputs") for r in results) else 1


def cmd_exp_status(args) -> int:
    runner.print_status(challenge=args.challenge, recent=args.recent)
    return 0


def cmd_report(args) -> int:
    run_dir = Path(args.run_dir).expanduser()
    if not run_dir.exists():
        print(f"no such run dir: {run_dir}")
        return 1
    print(report_html.render_run_report(run_dir))
    return 0


def cmd_dashboard(args) -> int:
    out = Path(args.out).expanduser() if args.out else common.PROJECT_ROOT / "runs-dashboard.html"
    print(report_html.render_dashboard(out, challenge=args.challenge))
    return 0


def cmd_serve(args) -> int:
    from tools.serve import app as serve_app

    serve_app.run(port=args.port, open_browser=args.open)
    return 0


def cmd_export(args) -> int:
    from tools.serve import export as export_mod

    return export_mod.run(Path(args.out).expanduser())


def cmd_movie(args) -> int:
    from tools.report import movie as movie_mod

    run_dir = Path(args.run_dir).expanduser()
    if not run_dir.is_dir():
        print(f"no such run dir: {run_dir}")
        return 1
    out = movie_mod.render_movie(run_dir, index=args.index, out=args.out,
                                 frames=args.frames, mode=args.mode,
                                 design=args.design, seed=args.seed,
                                 workers=args.workers, fps=args.fps,
                                 style=args.style)
    print(f"movie: {out}")
    return 0


def cmd_device(args) -> int:
    print(devices.describe())
    return 0


def cmd_fetch_data(args) -> int:
    baseline = common.SOURCE_REPOS["baseline"]
    challenges = common.CHALLENGES_DIR
    plans = [
        (baseline / "challenges/02-tnfa/data/1TNF.cif", challenges / "02-tnfa/inputs/1TNF.cif", "file"),
        (baseline / "challenges/02-tnfa/data/target_AB.pdb", challenges / "02-tnfa/inputs/target_AB.pdb", "file"),
        (baseline / "challenges/02-tnfa/data/human_tnf.fasta", challenges / "02-tnfa/inputs/human_tnf.fasta", "file"),
        (baseline / "challenges/02-tnfa/data/mouse_tnf.fasta", challenges / "02-tnfa/inputs/mouse_tnf.fasta", "file"),
    ]
    if not baseline.exists():
        print(f"source repo not found: {baseline}\n(set PDT_BASELINE_REPO to override)")
        return 1
    copied = skipped = missing = 0
    for src, dst, kind in plans:
        if not src.exists():
            missing += 1
            print(f"missing source: {src}")
            continue
        if dst.exists() and not args.force:
            skipped += 1
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if kind == "dir":
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
        copied += 1
        print(f"copied {src} -> {dst}")
    print(f"\n{copied} copied, {skipped} skipped (already present; --force to overwrite), {missing} missing")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pdt", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    exp = sub.add_parser("exp", help="experiment commands")
    exp_sub = exp.add_subparsers(dest="action", required=True)

    p = exp_sub.add_parser("list", help="list experiments")
    p.add_argument("--challenge")
    p.set_defaults(func=cmd_exp_list)

    p = exp_sub.add_parser("run", help="run experiments")
    p.add_argument("names", nargs="*", help="experiment names (default with --all)")
    p.add_argument("--all", action="store_true")
    p.add_argument("--challenge")
    p.add_argument("-j", "--jobs", type=int, default=2, help="parallel experiments (default 2)")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_exp_run)

    p = exp_sub.add_parser("status", help="recent runs")
    p.add_argument("--challenge")
    p.add_argument("--recent", type=int, default=15)
    p.set_defaults(func=cmd_exp_status)

    p = sub.add_parser("report", help="(re)build a run's HTML report")
    p.add_argument("run_dir")
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("dashboard", help="hub HTML (challenge -> experiment -> 3D)")
    p.add_argument("--out")
    p.add_argument("--challenge")
    p.set_defaults(func=cmd_dashboard)

    p = sub.add_parser("serve", help="local web app: hub, reports, 3Dmol viewer")
    p.add_argument("--port", type=int, default=8737)
    p.add_argument("--open", action="store_true", help="open the browser automatically")
    p.set_defaults(func=cmd_serve)

    p = sub.add_parser("export", help="build the static site for the Cloudflare Worker (site/dist)")
    p.add_argument("--out", default="site/dist")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("movie", help="MP4 of a run's structure (MD trajectory, sim physics, dock, spin)")
    p.add_argument("run_dir")
    p.add_argument("--index", type=int, default=0,
                   help="structure index in the run's viewer list (0 = first)")
    p.add_argument("--frames", type=int, default=36)
    p.add_argument("--mode", choices=["auto", "trajectory", "sim", "dock", "spin"], default="auto",
                   help="auto: trajectory for a multi-model structure, else sim when "
                        "linkage scores and a binder chain exist, else dock, else spin")
    p.add_argument("--style", choices=["cartoon", "cloud", "surface"], default="cartoon",
                   help="cartoon ribbons, a cloud of one dot per atom, or the molecular surface")
    p.add_argument("--design", help="design name for the simulation (default: the "
                                    "selected structure's own design)")
    p.add_argument("--seed", type=int, help="random seed of the simulation")
    p.add_argument("--workers", type=int, help="parallel Chrome renderers (default 3)")
    p.add_argument("--fps", type=int, help="frames per second (default 18 for sim, 12 else)")
    p.add_argument("--out")
    p.set_defaults(func=cmd_movie)

    p = sub.add_parser("device", help="cpu / mps / cuda availability")
    p.set_defaults(func=cmd_device)

    p = sub.add_parser("fetch-data", help="copy the public target files into challenges/*/inputs")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_fetch_data)

    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
