#!/usr/bin/env python3
"""A still of the whole receptor: the TfR1 dimer with a design on both tips.

The reel shows one protomer, which leaves out the three things the full
receptor says.  It is a disulfide-linked homodimer, so every target carries two
copies of the epitope, 82 A apart.  Our patch is the furthest point on it from
the cell membrane - the apical domain is the tip, and the epitope sits at the
tip of the tip, pointing away from the cell.  And a 76-residue design against a
1,278-residue receptor is a size difference a cropped view hides.

Structures: the crystal dimer (inputs/11QC.cif) gives the receptor and the
frame; each design's own Chai-1 co-fold gives the binder, superposed onto each
protomer in turn.  Nothing here is predicted that was not already predicted.

    .venv/bin/python challenges/04-tfr1/videos/scripts/dimer_still.py

Stages: prep (place everything), render (one Blender frame), compose (the
backdrop, the legend and the membrane line, laid together).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image
from Bio.PDB import MMCIFParser, PDBIO, Superimposer
from Bio.PDB.Polypeptide import protein_letters_3to1 as THREE_TO_ONE

REPO = Path(__file__).resolve().parents[4]
CH4 = REPO / "challenges/04-tfr1"
DIMER = CH4 / "inputs/11QC.cif"
TOP20 = CH4 / "records/selection-top20-2026-10-30.csv"
CHAI = Path.home() / "c4-work/chai/designs"
HUMAN = Path.home() / "c4-work/targets/human_full.fa"
WORK = Path.home() / "c4-work/dimer-still"
OUT = CH4 / "videos/out/04-tfr1-dimer.png"
RENDER_PY = Path(__file__).with_name("dimer_render.py")

TOP = 10                            # placed in prep; the still draws the first
WIDTH, HEIGHT = 1920, 1080          # the finished image
MOL_W, MOL_H = 1920, 690            # the Blender render, laid over the backdrop
MOL_Y = 230                         # its top edge: clear of the title above,
                                    # and leaving the foot for the membrane

# Domain boundaries are the published ones (Lawrence et al. 1999, PDB 1CX8
# numbering, which 11QC shares).  Checked against the structure before use:
# along the dimer's own two-fold axis the apical domain sits 20 A clear of the
# centre on the far side from the membrane, the protease-like domain 12 A on
# the near side, and the helical domain spans the middle as the dimer core.
DOMAINS = [("apical domain", "resid 189-383", "#9fb4d0"),
           ("helical domain", "resid 607-760", "#9a9478"),
           ("protease-like domain", "resid 121-188 384-606", "#9c7d80")]
BINDER_HUE = "#d6467f"              # the champion's accent in the reel

CHROME = os.environ.get("PDT_CHROME") or os.environ.get("CHROME_PATH") or str(
    Path.home() / ".cache/ms-playwright/chromium-1243/chrome-linux64/chrome")


def designs() -> list[dict]:
    with TOP20.open() as fh:
        return [{"rank": i + 1, "name": r["design"], "score": float(r["score"])}
                for i, r in enumerate(list(csv.DictReader(fh))[:TOP])]


def sequence(chain) -> dict[int, str]:
    return {r.id[1]: THREE_TO_ONE.get(r.get_resname(), "X")
            for r in chain if r.id[0] == " "}


def model_cif(name: str) -> Path:
    """The design's best restrained co-fold, as the reel picks it."""
    out_dir = CHAI / name / "out"
    if not out_dir.is_dir():
        raise SystemExit(f"no human chai fold for {name} at {out_dir}")
    best, best_iptm = None, -1.0
    for cif in sorted(out_dir.glob("pred.model_idx_*.cif")):
        idx = cif.stem.split("_")[-1]
        iptm = np.load(out_dir / f"scores.model_idx_{idx}.npz")["iptm"].item()
        if iptm > best_iptm:
            best, best_iptm = cif, iptm
    return best


def solve_offset(crystal: dict[int, str], fold: dict[int, str]) -> int:
    """How far the co-fold's 1-based numbering is shifted from the crystal's.

    Chai renumbers its chains from 1 and the construct does not start where the
    crystal does, so the two have to be matched on sequence rather than assumed
    to line up.  Scanning a few offsets is enough: the right one matches almost
    every residue and the wrong ones match about one in twenty.
    """
    best, score = None, -1.0
    for offset in range(-10, 11):
        pairs = [(crystal[r], fold[r - 121 + offset]) for r in crystal
                 if (r - 121 + offset) in fold]
        if len(pairs) < 100:
            continue
        hit = sum(a == b for a, b in pairs) / len(pairs)
        if hit > score:
            best, score = offset, hit
    if score < 0.95:
        raise SystemExit(f"co-fold does not match the crystal (best {score:.2f})")
    print(f"[prep] co-fold numbering offset {best:+d} ({score:.1%} identical)")
    return best


def upright(chain_a, chain_b) -> tuple[np.ndarray, np.ndarray]:
    """Centre the dimer and stand it the way the textbook figures draw it.

    The two-fold axis is the membrane normal, so it goes vertical with the
    membrane side down; the vector between the two protomers goes across the
    screen, which puts one apical tip at each top corner.
    """
    a = np.array([r["CA"].coord for r in chain_a if r.id[0] == " " and "CA" in r])
    b = np.array([r["CA"].coord for r in chain_b if r.id[0] == " " and "CA" in r])
    centre = np.vstack([a, b]).mean(axis=0)
    # the two-fold is the eigenvector of the A->B rotation with eigenvalue 1
    u, _, vt = np.linalg.svd((a - a.mean(0)).T @ (b - b.mean(0)))
    flip = np.diag([1.0, 1.0, float(np.sign(np.linalg.det(vt.T @ u.T)))])
    rot = vt.T @ flip @ u.T
    values, vectors = np.linalg.eig(rot)
    axis = np.real(vectors[:, np.argmin(np.abs(values - 1))])
    axis /= np.linalg.norm(axis)
    helical = np.array([r["CA"].coord for r in chain_a
                        if r.id[0] == " " and "CA" in r and 607 <= r.id[1] <= 760])
    if (helical.mean(0) - centre) @ axis < 0:
        axis = -axis                       # +axis now points at the membrane
    across = b.mean(0) - a.mean(0)
    across = across - (across @ axis) * axis
    across /= np.linalg.norm(across)
    frame = np.vstack([across, np.cross(-axis, across), -axis])   # rows: X, Y, Z
    if np.linalg.det(frame) < 0:
        frame[1] = -frame[1]
    return frame, centre


def prep(rows: list[dict], force: bool = False) -> None:
    out_dir = WORK / "structures"
    if out_dir.exists() and not force:
        print(f"[prep] reusing {out_dir}")
        return
    out_dir.mkdir(parents=True, exist_ok=True)
    parser = MMCIFParser(QUIET=True)
    crystal = parser.get_structure("dimer", str(DIMER))[0]
    frame, centre = upright(crystal["A"], crystal["B"])
    for atom in crystal.get_atoms():
        atom.set_coord(frame @ (atom.coord - centre))
    io = PDBIO()
    io.set_structure(crystal)
    io.save(str(out_dir / "dimer.pdb"), ChainSelect("AB"))

    crystal_seq = sequence(crystal["A"])
    for row in rows:
        fold = parser.get_structure(row["name"], str(model_cif(row["name"])))[0]
        if row["rank"] == 1:
            offset = solve_offset(crystal_seq, sequence(fold["A"]))
        pairs = [(r, r - 121 + offset) for r in sorted(crystal_seq)]
        for protomer in "AB":
            moving = parser.get_structure("m", str(model_cif(row["name"])))[0]
            fixed = [crystal[protomer][r]["CA"] for r, f in pairs
                     if f in moving["A"] and "CA" in moving["A"][f]]
            mobile = [moving["A"][f]["CA"] for r, f in pairs
                      if f in moving["A"] and "CA" in moving["A"][f]]
            sup = Superimposer()
            sup.set_atoms(fixed, mobile)
            sup.apply(moving.get_atoms())
            io = PDBIO()
            io.set_structure(moving["B"])
            io.save(str(out_dir / f"binder-{row['rank']:02d}{protomer}.pdb"))
        print(f"[prep] {row['rank']:2d}  {row['name']}  rms {sup.rms:.2f} A")


class ChainSelect:
    """PDBIO selector keeping only the named chains."""

    def __init__(self, chains: str):
        self.chains = set(chains)

    def accept_model(self, model):
        return 1

    def accept_chain(self, chain):
        return int(chain.id in self.chains)

    def accept_residue(self, residue):
        return int(residue.id[0] == " ")

    def accept_atom(self, atom):
        return 1


# ------------------------------------------------------------------ backdrop

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1920px;height:1080px;
  background:#0a0e14 radial-gradient(1100px 820px at 50% 44%,#18222f 0%,#0a0e14 74%);
  font-family:-apple-system,'Segoe UI','Liberation Sans','DejaVu Sans',sans-serif;
  color:#e9edf3;-webkit-font-smoothing:antialiased}
.top{position:absolute;left:96px;top:72px}
.eyebrow{font-size:15px;font-weight:700;letter-spacing:3.4px;color:#78839a}
h1{font-size:38px;font-weight:600;letter-spacing:-.7px;margin-top:14px}
.sub{font-size:17px;color:#78839a;margin-top:12px;line-height:1.5}
.key{position:absolute;right:96px;top:80px;text-align:right;font-size:15px;
  color:#9aa3b4;line-height:2.1}
.key i{display:inline-block;width:11px;height:11px;border-radius:3px;
  margin-left:12px;vertical-align:1px}
.membrane{position:absolute;left:0;width:1920px;height:0;
  border-top:2px dashed rgba(233,237,243,.22)}
.membrane span{position:absolute;right:96px;top:14px;font-size:14px;
  letter-spacing:2.4px;color:#5d6678}
.foot{position:absolute;left:96px;right:96px;bottom:40px;font-size:15px;
  color:#5d6678;display:flex;justify-content:space-between}
.foot em{color:#9a7b45;font-style:normal}
"""


def backdrop_html(row: dict, membrane_y: int) -> str:
    key = "".join(f'<div>{name}<i style="background:{hue}"></i></div>'
                  for name, _, hue in DOMAINS)
    key += f'<div>the design<i style="background:{BINDER_HUE}"></i></div>'
    return f"""<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<body>
<div class="membrane" style="top:{membrane_y}px"><span>PLASMA MEMBRANE</span></div>
<div class="top">
<div class="eyebrow">TfR1 &middot; CHALLENGE 04</div>
<h1>Two epitopes per receptor</h1>
<div class="sub">human transferrin receptor 1 ectodomain, the disulfide-linked
homodimer<br>our design on both apical tips &middot; the two sites sit 82 &Aring;
apart</div></div>
<div class="key">{key}</div>
<div class="foot">
<span><em>{row['name']}</em> &middot; 76 aa against 1,278 &middot; crystal dimer
11QC with the design&rsquo;s own Chai-1 co-fold superposed on each protomer</span>
<span>linkedin.com/in/anton-chernysh</span></div></body>"""


def shoot(html: str, path: Path) -> None:
    page = WORK / "backdrop.html"
    page.write_text(html)
    subprocess.run(
        [CHROME, "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
         "--force-device-scale-factor=1", f"--window-size={WIDTH},{HEIGHT}",
         f"--screenshot={path}", page.as_uri()],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# -------------------------------------------------------------------- render

def blender(rank: int) -> Path:
    frames = WORK / "frames"
    spec = {"structures": str(WORK / "structures"), "frames": str(frames),
            "rank": rank, "width": MOL_W, "height": MOL_H,
            "domains": [[sel, hue] for _, sel, hue in DOMAINS],
            "binder": BINDER_HUE}
    (WORK / "spec.json").write_text(json.dumps(spec))
    subprocess.run(["blender", "-b", "--python", str(RENDER_PY),
                    "--", str(WORK / "spec.json")], check=True)
    return frames / "frame_0000.png"


def compose(rows: list[dict], rank: int) -> None:
    """Lay the render over the backdrop, with the membrane at the molecule's foot."""
    molecule = Image.open(blender(rank)).convert("RGBA")
    box = molecule.getchannel("A").getbbox()
    if box is None:
        raise SystemExit("the render is empty")
    membrane_y = MOL_Y + box[3] + 26
    plate = WORK / "backdrop.png"
    shoot(backdrop_html(rows[rank - 1], membrane_y), plate)
    page = Image.open(plate).convert("RGBA")
    page.alpha_composite(molecule, (0, MOL_Y))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    page.convert("RGB").save(OUT)
    print(f"[compose] molecule spans {box[2]-box[0]}x{box[3]-box[1]} px, "
          f"membrane at y={membrane_y}")
    print(f"[compose] {OUT}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", nargs="?", default="all",
                    choices=["all", "prep", "compose"])
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--rank", type=int, default=1, help="which design to draw")
    args = ap.parse_args()
    rows = designs()
    if args.stage in ("all", "prep"):
        prep(rows, args.force)
    if args.stage in ("all", "compose"):
        compose(rows, args.rank)


if __name__ == "__main__":
    main()
