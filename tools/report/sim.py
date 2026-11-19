"""Coarse-grained binding simulation for the movie renderer.

This module holds the physics behind the `sim` movie mode. The model is a
rigid-body overdamped Langevin (Brownian) simulation of one designed binder
against its target. The reaction coordinate is the distance between the
binder and its predicted docked pose.

The potential comes from the pipeline's own measurement: the PROPKA
pH-linkage term (`ddg_ph_low`, `ddg_ph_high`, `ph_selectivity_kcal` in the
run's `ph_scores.csv` / `mutant_metrics.csv`).

The energy model mirrors the pipeline's own two-state math: the binding
energy applies inside the contact zone (r < radius), nothing applies
outside it, and a narrow smooth edge joins the two states. A negative well
pulls the binder in (the pH-favoured state). A positive well forms a soft
barrier on the contact edge (the binder is turned away).

Honesty rules (state these in every caption that uses this module):

- The wells are mean-centred. Only the pH-dependent part of the binding
  energy is modeled. The absolute affinity is not measured by this pipeline
  and is not shown.
- PROPKA linkage scores rank candidates. They do not predict real affinities.
- This is not all-atom molecular dynamics. It is a two-body stochastic model
  on a score-derived potential.

Units: distances in Angstrom, energies in kcal/mol and in kT. One kT is
0.5922 kcal/mol at 298 K.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

KCAL_PER_KT = 0.5922  # RT at 298 K, kcal/mol


def kcal_to_kt(kcal: float) -> float:
    """Convert kcal/mol to kT at the model temperature."""
    return float(kcal) / KCAL_PER_KT


def well_values_kcal(selectivity_kcal: float) -> tuple[float, float]:
    """The two pH wells in kcal/mol, mean-centred on zero.

    The measured selectivity is ddg(ph_low) - ddg(ph_high). The wells shown
    in the simulation keep this difference exactly:

        well(ph_low)  = selectivity / 2
        well(ph_high) = -selectivity / 2

    A negative well favours the contact (the binder is pulled in). A
    positive well disfavours it (the binder is turned away at the edge).
    """
    selectivity = float(selectivity_kcal)
    return selectivity / 2.0, -selectivity / 2.0


def potential_kcal(r, well_kcal: float, radius: float = 5.5, edge: float = 0.4):
    """Interaction energy at distance `r` from the docked pose.

    `well_kcal` deep inside the contact radius, zero far outside it, joined
    by a smooth sigmoid edge of width `edge`. `r` can be a scalar or an
    array.
    """
    r = np.asarray(r, dtype=float)
    return well_kcal / (1.0 + np.exp((r - radius) / edge))


def potential_gradient_kcal(r: float, well_kcal: float,
                            radius: float = 5.5, edge: float = 0.4) -> float:
    """dU/dr at distance `r`, kcal/mol per Angstrom."""
    z = (r - radius) / edge
    sigmoid = 1.0 / (1.0 + np.exp(-z))
    return -well_kcal * sigmoid * (1.0 - sigmoid) / edge


@dataclass
class SimParams:
    """All knobs of the simulation. Defaults are tuned for a ~12 s movie."""

    n_frames: int = 210
    substeps: int = 14
    step_rms: float = 0.55       # A per substep: sqrt(2 D dt)
    box_radius: float = 17.0     # A, soft reflecting wall around the pose
    start_offset: float = 13.0   # A, binder starts this far from the pose
    contact_radius: float = 5.5  # A, the contact zone edge (the well radius)
    edge: float = 0.4            # A, width of the smooth well edge
    seed: int = 7


@dataclass
class Frame:
    """One recorded movie frame of the binder position."""

    index: int
    offset: np.ndarray            # binder displacement from the docked pose, A
    r: float                      # |offset|, A
    ph: float
    well_kcal: float
    contact: bool
    phase: int                    # index into the pH schedule


@dataclass
class SimResult:
    frames: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    wells: dict = field(default_factory=dict)
    schedule: list = field(default_factory=list)
    curves: dict = field(default_factory=dict)
    params: SimParams = field(default_factory=SimParams)


def _phase_counts(n_frames: int, schedule: list) -> list:
    """Frame count per schedule entry; the last entry absorbs rounding."""
    fractions = [fraction for _ph, fraction in schedule]
    total = sum(fractions)
    if total <= 0:
        raise ValueError("schedule fractions must be positive")
    counts = [int(round(n_frames * fraction / total)) for fraction in fractions[:-1]]
    counts.append(n_frames - sum(counts))
    return counts


def simulate(params: SimParams | None = None,
             wells: dict | None = None,
             schedule: list | None = None) -> SimResult:
    """Run the simulation and return frames plus per-phase statistics.

    `wells` maps pH value -> well depth in kcal/mol, for example
    {6.5: -0.441, 7.4: +0.441}. `schedule` is a list of (pH, fraction)
    entries, for example [(6.5, 0.45), (7.4, 0.55)].
    """
    p = params or SimParams()
    wells = wells or {}
    schedule = schedule or [(6.5, 0.5), (7.4, 0.5)]
    for ph, _fraction in schedule:
        if ph not in wells:
            raise KeyError(f"no well value for pH {ph} — pass wells for every schedule pH")

    counts = _phase_counts(p.n_frames, schedule)
    if any(count < 1 for count in counts):
        raise ValueError("every pH phase needs at least one frame")

    rng = np.random.default_rng(p.seed)
    drift_coeff = p.step_rms**2 / 2.0  # D dt, A^2 per substep

    pos = np.array([p.start_offset, 0.0, 0.0])
    frames = []
    # per-phase bookkeeping: [frames_total, frames_contact, events, dwell, longest]
    phase_stats = [[0, 0, 0, 0, 0] for _ in schedule]
    in_contact = False
    dwell = 0

    for phase_index, (ph, _fraction) in enumerate(schedule):
        well = float(wells[ph])
        for _ in range(counts[phase_index]):
            for _ in range(p.substeps):
                r_now = float(np.linalg.norm(pos))
                # dU/dr in kcal/mol per A; the force acts along -r_hat.
                grad = potential_gradient_kcal(r_now, well, p.contact_radius, p.edge)
                grad_kt = grad / KCAL_PER_KT  # 1/A, energy in kT
                pos = pos - drift_coeff * grad_kt * (pos / max(r_now, 1e-9))
                pos = pos + p.step_rms * rng.normal(size=3)
                length = float(np.linalg.norm(pos))
                if length > p.box_radius:
                    # soft reflection back inside the box
                    pos = pos * ((2.0 * p.box_radius - length) / length)
                if not np.all(np.isfinite(pos)):
                    raise FloatingPointError("simulation diverged")

            r_now = float(np.linalg.norm(pos))
            contact = r_now < p.contact_radius
            frames.append(Frame(index=len(frames), offset=pos.copy(), r=r_now,
                                ph=ph, well_kcal=well, contact=contact,
                                phase=phase_index))
            entry = phase_stats[phase_index]
            entry[0] += 1
            if contact:
                entry[1] += 1
                dwell += 1
                entry[4] = max(entry[4], dwell)
                if not in_contact:
                    entry[2] += 1  # a fresh binding event
                in_contact = True
            else:
                if in_contact:
                    entry[3] += dwell
                    dwell = 0
                in_contact = False
        if in_contact:
            # a dwell that runs into the pH switch still counts
            phase_stats[phase_index][3] += dwell
            dwell = 0

    stats = {"phases": [], "n_frames": p.n_frames}
    for index, (ph, _fraction) in enumerate(schedule):
        total, contact_frames, events, dwell_frames, longest = phase_stats[index]
        stats["phases"].append({
            "ph": ph,
            "well_kcal": round(float(wells[ph]), 4),
            "well_kt": round(kcal_to_kt(float(wells[ph])), 3),
            "frames": total,
            "contact_frames": contact_frames,
            "occupancy": round(contact_frames / total, 4) if total else 0.0,
            "binding_events": events,
            "mean_dwell_frames": round(dwell_frames / events, 1) if events else 0.0,
            "longest_dwell_frames": longest,
        })

    curves = {}
    grid = np.arange(0.0, p.box_radius + 1e-9, 0.25)
    for ph, well in wells.items():
        curves[float(ph)] = [(float(r), float(potential_kcal(r, float(well),
                                                             p.contact_radius, p.edge)))
                             for r in grid]

    return SimResult(frames=frames, stats=stats, wells=dict(wells),
                     schedule=[tuple(item) for item in schedule], params=p,
                     curves=curves)


def analytic_occupancy(well_kcal: float, radius: float = 5.5, edge: float = 0.4,
                       box_radius: float = 17.0) -> float:
    """Equilibrium contact probability for the exact model potential.

    The stationary density of the overdamped Langevin process is
    proportional to exp(-U(r)/kT), so the contact occupancy is a radial
    Boltzmann integral. The tests compare the simulation against this value.
    """
    r = np.linspace(0.0, box_radius, 8000)
    weight = np.exp(-potential_kcal(r, well_kcal, radius, edge) / KCAL_PER_KT) * 4.0 * np.pi * r**2
    inside = r <= radius
    total = float(weight.sum())
    if total <= 0:
        return 0.0
    return float(weight[inside].sum()) / total
