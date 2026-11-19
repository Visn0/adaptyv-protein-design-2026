#!/usr/bin/env python3
"""A few seconds of Chai-1 building one design's fold.

This is not protein folding, and the clip has to be captioned as such.  Chai-1
is a diffusion model: it starts from a cloud of random atom positions and
denoises it over 200 steps, emitting at every step its current best guess at
the finished structure.  What this records and plays back is that sequence of
guesses - the model's route to an answer, not states the molecule passes
through.  Nothing available here shows real folding; that is microseconds to
milliseconds of dynamics and months of specialised GPU time.

Stages:

    trace    the GPU run, recording every guess        (chai venv)
    build    align the guesses, write traj.pdb         (repo venv)
    panels   the backdrop and its caption              (repo venv)
    preview  one frame, composited                     (repo venv)
    render   blender + ffmpeg                          (repo venv)

    ~/.venvs/chai/bin/python challenges/04-tfr1/videos/scripts/fold_movie.py trace
    .venv/bin/python challenges/04-tfr1/videos/scripts/fold_movie.py render

Only `trace` needs the chai venv, and it imports nothing from the rest of this
file beyond the sequence lookup.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
CH4 = REPO / "challenges/04-tfr1"
SUBMISSION = CH4 / "submission/submission-04-tfr1.csv"
WORK = Path.home() / "c4-work/fold-movie"
OUT = CH4 / "videos/out/04-tfr1-fold.mp4"
RENDER_PY = Path(__file__).with_name("fold_render.py")

DESIGN = "c3_e12rfd4_r4d5_d2"     # the champion; rank 1 of the twenty
COLOR = "#d6467f"                 # its accent in the reel
STEPS = 200                       # Chai's default; two denoiser calls each
SECS = 4.0
FPS = 24
TURN_DEG = 40.0                   # a slow turn under the folding, for depth
START_SIGMA = 12.0                # A; where the clip starts on the noise schedule
WIDTH, HEIGHT = 1280, 720
SCALE = 1.5
VW, VH = int(WIDTH * SCALE), int(HEIGHT * SCALE)
MOL = int(680 * SCALE)            # the square Blender render
MOL_Y = int(28 * SCALE)

CHROME = os.environ.get("PDT_CHROME") or os.environ.get("CHROME_PATH") or str(
    Path.home() / ".cache/ms-playwright/chromium-1243/chrome-linux64/chrome")


def binder_sequence() -> str:
    """The submitted sequence for DESIGN, read without importing anything heavy."""
    import csv
    with SUBMISSION.open() as fh:
        for row in csv.DictReader(fh):
            if row["name"] == DESIGN:
                return row["sequence"]
    raise SystemExit(f"{DESIGN} is not in {SUBMISSION}")


# --------------------------------------------------------------------- trace

def trace() -> None:
    """Fold the binder alone, keeping every intermediate the model emits.

    The diffusion module is the only one called with noised coordinates, so
    that keyword identifies its calls; what it returns is the current guess at
    the clean structure, which is what we want to watch.  Its noise level comes
    back too, because the schedule is far from linear and the sampling in
    `build` needs it.
    """
    import numpy as np
    import chai_lab.chai1 as chai1

    WORK.mkdir(parents=True, exist_ok=True)
    fasta = WORK / "in.fasta"
    fasta.write_text(f">protein|A\n{binder_sequence()}\n")
    out_dir = WORK / "out"
    if out_dir.exists():
        raise SystemExit(f"{out_dir} exists; remove it to re-trace")

    states: list[np.ndarray] = []     # the sampler's own noisy structure
    sigmas: list[float] = []
    original = chai1.ModuleWrapper.forward

    def recording(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        if "atom_noised_coords" in kwargs:
            # What goes in, not what comes back.  The input is the sampler's
            # own state - noise at first, the structure at the end - and the
            # only one of the two that visibly moves; the returned guess is
            # within half an angstrom of the final fold from the very first
            # step, because the trunk settles the structure before diffusion
            # starts, and it comes back in a frame of the model's own choosing
            # rather than the input's.
            states.append(one(kwargs["atom_noised_coords"]))
            sigmas.append(float(kwargs["noise_sigma"].flatten()[0]))
        return result

    chai1.ModuleWrapper.forward = recording
    try:
        chai1.run_inference(
            fasta_file=fasta, output_dir=out_dir,
            num_trunk_recycles=3, num_diffn_timesteps=STEPS,
            num_diffn_samples=1, num_trunk_samples=1,
            # as every other Chai run in this challenge: the ESM weights are a
            # 5.6 GB download this box has never held, and a de novo binder has
            # no homologs for an MSA to find anyway
            use_esm_embeddings=False, seed=7, device="cuda:0")
    finally:
        chai1.ModuleWrapper.forward = original

    if not states:
        raise SystemExit("no diffusion calls were recorded")
    np.save(WORK / "states.npy", np.stack(states))
    (WORK / "sigmas.json").write_text(json.dumps(sigmas))
    print(f"[trace] {len(states)} steps, {states[0].shape[0]} atoms, "
          f"sigma {sigmas[0]:.1f} -> {sigmas[-1]:.3f}")


def one(tensor):
    """One sample's (atoms, 3) out of whatever leading dimensions Chai used."""
    array = tensor.detach().float().cpu().numpy()
    return array.reshape(-1, *array.shape[-2:])[0]


# --------------------------------------------------------------------- build

def build() -> None:
    """Sample the guesses, put them in one frame, write a multi-model PDB.

    Two things have to be fixed before this plays as an animation.  The sampler
    re-centres and randomly rotates the coordinates at every step, so each
    recorded guess is in its own frame and consecutive ones would jump; and the
    noise schedule is steeply non-linear, so sampling by step index would spend
    most of the clip on a structure that has already stopped moving.  So: align
    each guess onto the one after it, backwards from the last, which leaves the
    final frame in the structure's own orientation; and sample evenly in log
    noise, which spreads the visible change across the whole clip.
    """
    import numpy as np
    from Bio.PDB import MMCIFParser, PDBIO, Structure

    states = np.load(WORK / "states.npy")
    sigmas = np.array(json.loads((WORK / "sigmas.json").read_text()))
    cif = next((WORK / "out").glob("pred.model_idx_*.cif"))
    model = MMCIFParser(QUIET=True).get_structure(DESIGN, str(cif))[0]
    atoms = list(model.get_atoms())
    if states.shape[1] < len(atoms):
        raise SystemExit(f"{states.shape[1]} traced atoms < {len(atoms)} in {cif.name}")
    states = states[:, :len(atoms)]            # the rest is crop padding

    # The schedule opens at sigma 1260, where the cloud is a hundred times the
    # size of the protein and nothing can be framed with it in shot, so start
    # where it is a few times the fold instead.
    first = int(np.argmax(sigmas <= START_SIGMA))

    # Put every step into one coordinate frame before anything else: the
    # sampler re-centres and randomly rotates at each one, so each state
    # arrives in its own.  Fit each state onto the next, backwards from the
    # last, so the whole run ends up in the finished fold's orientation.  The
    # noise makes each fit imperfect, but 550 atoms average it out to well
    # under a degree, and consecutive states share nearly all their structure.
    for i in range(len(states) - 2, first - 1, -1):
        rot, moving, fixed = kabsch(states[i], states[i + 1])
        states[i] = (states[i] - moving) @ rot.T + fixed

    # Then resample.  Only ~160 steps are left after the cut and the fold is in
    # place within the first forty of them, so choosing steps - by noise, by
    # number or by distance - spends the clip on a couple of dozen distinct
    # poses, each held for several frames.  Interpolating along the path at
    # evenly spaced distances to the answer gives every frame its own pose and
    # an even rate of collapse on screen.
    path, goal = states[first:], states[-1]
    gap = np.minimum.accumulate(np.linalg.norm(path - goal, axis=2).mean(axis=1))
    keep = np.concatenate(([True], np.diff(gap) < -1e-6))
    gap, path = gap[keep], path[keep]
    targets = np.linspace(gap[0], gap[-1], int(SECS * FPS))
    flat = path[::-1].reshape(len(path), -1)
    frames = np.stack([np.interp(targets, gap[::-1], flat[:, k])
                       for k in range(flat.shape[1])], axis=1)
    frames = frames.reshape(len(targets), -1, 3)
    print(f"[build] {len(path)} usable steps -> {len(frames)} interpolated frames")

    # Put the finished fold on the origin.  The turn in the render spins the
    # whole thing about Z, so anything off-centre is swung round in an arc
    # instead of rotating in place - which widens the box every frame has to
    # share and leaves the payoff frame small and off to one side.
    frames -= frames[-1].mean(axis=0)

    traj = Structure.Structure("traj")
    for i, coords in enumerate(frames):
        snapshot = copy.deepcopy(model)
        snapshot.id, snapshot.serial_num = i, i + 1
        for atom, xyz in zip(snapshot.get_atoms(), coords):
            atom.set_coord(xyz)
        traj.add(snapshot)
    io = PDBIO()
    io.set_structure(traj)
    io.save(str(WORK / "traj.pdb"))

    radii = [float(np.linalg.norm(f - f.mean(axis=0), axis=1).mean()) for f in frames]
    print(f"[build] {len(frames)} frames, {len(atoms)} atoms, "
          f"mean radius {radii[0]:.1f} -> {radii[-1]:.1f} A")
    check_final(model, frames[-1], atoms)


def check_final(model, final, atoms) -> None:
    """How close the clip's last frame is to the fold we actually submitted.

    This run is single-sequence and MSA-free, so the structure it lands on is
    its own; if it disagrees with the co-fold the design was selected on, the
    clip is showing the model building something else and should not be posted
    as that design.
    """
    import numpy as np
    from Bio.PDB import PDBParser
    known = Path.home() / "c4-work/mn-reel-v2/structures/binder-01.pdb"
    if not known.exists():
        print("[build] no reel structure to compare against; skipping the check")
        return
    mine = np.array([final[i] for i, a in enumerate(atoms) if a.name == "CA"])
    theirs = np.array([a.coord for a in
                       PDBParser(QUIET=True).get_structure("k", str(known))[0]
                       .get_atoms() if a.name == "CA"])
    if len(mine) != len(theirs):
        print(f"[build] {len(mine)} CA here vs {len(theirs)} in the reel; "
              "skipping the check")
        return
    rmsd = float(np.sqrt(((superpose(mine, theirs) - theirs) ** 2).sum(axis=1).mean()))
    verdict = "same fold" if rmsd < 3.0 else "DIFFERENT FOLD - do not post as this design"
    print(f"[build] final frame vs the submitted co-fold: {rmsd:.2f} A CA RMSD ({verdict})")


def kabsch(moving, reference):
    """The rotation and two centroids that put `moving` onto `reference`."""
    import numpy as np
    mc, rc = moving.mean(axis=0), reference.mean(axis=0)
    u, _, vt = np.linalg.svd((moving - mc).T @ (reference - rc))
    flip = np.diag([1.0, 1.0, float(np.sign(np.linalg.det(vt.T @ u.T)))])
    return vt.T @ flip @ u.T, mc, rc


def superpose(moving, reference):
    rot, mc, rc = kabsch(moving, reference)
    return (moving - mc) @ rot.T + rc


def rmsd(moving, reference):
    """How far `moving` is from `reference` once best fitted onto it."""
    import numpy as np
    fitted = superpose(moving, reference)
    return float(np.sqrt(((fitted - reference) ** 2).sum(axis=1).mean()))


# -------------------------------------------------------------------- panels

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1280px;height:720px;
  background:#0a0e14 radial-gradient(820px 640px at 50% 46%,#18222f 0%,#0a0e14 74%);
  font-family:-apple-system,'Segoe UI','Liberation Sans','DejaVu Sans',sans-serif;
  color:#e9edf3;-webkit-font-smoothing:antialiased}
.top{position:absolute;left:64px;top:52px}
.eyebrow{font-size:11px;font-weight:700;letter-spacing:2.4px;color:#78839a}
h1{font-size:26px;font-weight:600;letter-spacing:-.5px;margin-top:10px}
.sub{font-size:12px;color:#78839a;margin-top:8px;
  font-family:'DejaVu Sans Mono',ui-monospace,monospace}
.foot{position:absolute;left:64px;right:64px;bottom:40px;font-size:11px;
  color:#5d6678;display:flex;justify-content:space-between}
.foot em{color:#9a7b45;font-style:normal}
"""


def panel_html() -> str:
    return f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<body><div class="top">
<div class="eyebrow">TfR1 &middot; CHALLENGE 04</div>
<h1>How the model builds the fold</h1>
<div class="sub">{DESIGN} &middot; {len(binder_sequence())} aa</div>
</div>
<div class="foot">
<span><em>Chai-1 denoising, {STEPS} steps</em> &mdash; the model&rsquo;s route to a
structure, not the protein&rsquo;s</span>
<span>linkedin.com/in/anton-chernysh</span></div></body>"""


def shoot() -> None:
    out_dir = WORK / "panels"
    out_dir.mkdir(parents=True, exist_ok=True)
    page = WORK / "backdrop.html"
    page.write_text(panel_html())
    subprocess.run(
        [CHROME, "--headless", "--disable-gpu", "--no-sandbox",
         "--hide-scrollbars", f"--force-device-scale-factor={SCALE}",
         f"--window-size={WIDTH},{HEIGHT}",
         f"--screenshot={out_dir / 'backdrop.png'}", page.as_uri()],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[panels] {out_dir / 'backdrop.png'}")


# -------------------------------------------------------------------- render

def blender(frames: Path, only: int | None = None, start: int = 0) -> None:
    spec = {"traj": str(WORK / "traj.pdb"), "frames": str(frames),
            "color": COLOR, "size": MOL, "n_frames": int(SECS * FPS),
            "turn_deg": TURN_DEG, "only_frame": only, "start_frame": start}
    (WORK / "spec.json").write_text(json.dumps(spec))
    subprocess.run(["blender", "-b", "--python", str(RENDER_PY),
                    "--", str(WORK / "spec.json")], check=True)


def crop(frames: Path) -> str:
    """The box the molecule stays inside across every frame, plus a margin."""
    from PIL import Image
    boxes = [Image.open(p).getchannel("A").getbbox()
             for p in sorted(frames.glob("frame_*.png"))]
    boxes = [b for b in boxes if b]
    if not boxes:
        raise SystemExit(f"no opaque pixels in any frame under {frames}")
    x, y = min(b[0] for b in boxes), min(b[1] for b in boxes)
    w, h = max(b[2] for b in boxes) - x, max(b[3] for b in boxes) - y
    pad = 16
    x, y = max(0, x - pad), max(0, y - pad)
    w, h = min(MOL - x, w + 2 * pad), min(MOL - y, h + 2 * pad)
    print(f"[crop] crop={w}:{h}:{x}:{y}")
    return f"crop={w}:{h}:{x}:{y}"


def composite(frames: Path, first: int, count: int, out: Path) -> None:
    """Lay the molecule, centred, over the backdrop - preview and reel alike."""
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-loop", "1", "-framerate", str(FPS),
         "-i", str(WORK / "panels/backdrop.png"),
         "-framerate", str(FPS), "-start_number", str(first),
         "-i", str(frames / "frame_%04d.png"), "-frames:v", str(count),
         "-filter_complex",
         f"[1]{crop(frames)},scale=-1:{VH - 2 * MOL_Y}:flags=lanczos[m];"
         f"[0][m]overlay=(W-w)/2:{MOL_Y}:shortest=1,format=yuv420p",
         *([] if count == 1 else
           ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-r", str(FPS)]),
         str(out)], check=True)


def preview(frame: int) -> None:
    frames = WORK / "frames"
    if not (frames / f"frame_{frame:04d}.png").exists():
        frames = WORK / "preview-frames"
        blender(frames, only=frame)
    composite(frames, frame, 1, WORK / "preview.png")
    print(f"[preview] frame {frame}: {WORK / 'preview.png'}")


def render(force: bool = False) -> None:
    frames = WORK / "frames"
    n_frames = int(SECS * FPS)
    done = ({int(p.stem.split("_")[1]) for p in frames.glob("frame_*.png")}
            if frames.exists() else set())
    missing = [i for i in range(n_frames) if i not in done]
    if missing or force:
        start = 0 if force else missing[0]
        if start:
            print(f"[render] resuming at frame {start} of {n_frames}")
        blender(frames, start=start)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    composite(frames, 0, n_frames, OUT)
    print(f"[render] {OUT}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", nargs="?", default="render",
                    choices=["trace", "build", "panels", "preview", "render"])
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--frame", type=int, default=0)
    args = ap.parse_args()
    if args.stage == "trace":
        trace()
    elif args.stage == "build":
        build()
    elif args.stage == "panels":
        shoot()
    elif args.stage == "preview":
        preview(args.frame)
    else:
        render(args.force)


if __name__ == "__main__":
    main()
