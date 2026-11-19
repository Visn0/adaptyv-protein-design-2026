"""One OpenMM molecular-dynamics run of a prepared complex.

Real physics, stated plainly: AMBER14 force field, GBn2 implicit solvent,
300 K, Langevin dynamics, constraining all X-H bonds, 2 fs timestep.
Equilibration holds the backbone atoms with weak restraints. Production
runs free. The trajectory reports every atom, including hydrogens.

A short run like this is a physics test of the predicted pose. It is not a
binding assay, and it is not a free-energy calculation.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

from openmm import LangevinMiddleIntegrator, Platform, unit
from openmm.app import (CutoffNonPeriodic, DCDReporter, ForceField, HBonds,
                        Modeller, PDBFile, Simulation, StateDataReporter)

KCAL_TO_KJ = 4.184
BACKBONE_NAMES = ("N", "CA", "C", "O")


def pick_platform(log=print):
    """The fastest registered OpenMM platform. Override with PDT_MD_PLATFORM."""
    wanted = (os.environ.get("PDT_MD_PLATFORM") or "").strip() or None
    order = [wanted] if wanted else ["Metal", "OpenCL", "CPU"]
    notes = []
    for name in order:
        try:
            platform = Platform.getPlatformByName(name)
            log(f"md platform: {name}")
            return name, platform
        except Exception as exc:  # not registered on this build
            notes.append(f"{name} unavailable ({type(exc).__name__})")
    raise RuntimeError("no OpenMM platform available: " + ", ".join(notes))


def _build_forcefield():
    """AMBER14 for the protein plus the GBn2 implicit-solvent script."""
    return ForceField("amber14-all.xml", "implicit/gbn2.xml")


# The Debye screening parameter of a 1:1 salt in water at 298 K:
# kappa [1/nm] = 3.29 * sqrt(ionic strength [mol/L]).
KAPPA_PER_NM_PER_SQRT_MOLAR = 3.29


def kappa_per_nanometer(ionic_strength_molar: float) -> float:
    """Debye kappa in 1/nm for a 1:1 salt solution at 298 K."""
    return KAPPA_PER_NM_PER_SQRT_MOLAR * (max(float(ionic_strength_molar), 0.0) ** 0.5)


def _restraint_force(topology, positions, restraint_kcal: float, system):
    """Hold the backbone atoms near their start positions (equilibration only)."""
    from openmm import CustomExternalForce

    force = CustomExternalForce("0.5*k*((x-x0)^2+(y-y0)^2+(z-z0)^2)")
    force.addGlobalParameter("k", restraint_kcal * KCAL_TO_KJ * 100.0)  # kJ/mol/nm^2
    force.addPerParticleParameter("x0")
    force.addPerParticleParameter("y0")
    force.addPerParticleParameter("z0")
    for atom in topology.atoms():
        if atom.name in BACKBONE_NAMES:
            position = positions[atom.index].value_in_unit(unit.nanometer)
            force.addParticle(atom.index, [float(value) for value in position])
    system.addForce(force)
    return system


def _make_integrator(temperature_k: float, friction_per_ps: float, timestep_fs: float):
    """One Langevin integrator. Each context needs its own instance."""
    return LangevinMiddleIntegrator(temperature_k * unit.kelvin,
                                    friction_per_ps / unit.picosecond,
                                    timestep_fs / 1000.0 * unit.picoseconds)


def run_md(prepared_pdb, out_prefix, *, length_ps: float = 1000.0,
           save_every_ps: float = 5.0, equil_ps: float = 60.0,
           temperature_k: float = 300.0, friction_per_ps: float = 1.0,
           timestep_fs: float = 2.0, restraint_kcal: float = 5.0,
           seed: int = 7, ionic_strength_molar: float = 0.15,
           log=print) -> dict:
    """Run one trajectory. Returns paths plus timing and platform facts."""
    out_prefix = Path(out_prefix)
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    prepared_pdb = Path(prepared_pdb)

    pdb = PDBFile(str(prepared_pdb))
    modeller = Modeller(pdb.topology, pdb.positions)
    forcefield = _build_forcefield()
    modeller.addHydrogens(forcefield)
    topology = modeller.topology
    positions = modeller.positions
    n_atoms = topology.getNumAtoms()

    topology_path = Path(f"{out_prefix}_topology.pdb")
    with open(topology_path, "w") as handle:
        PDBFile.writeFile(topology, positions, handle)

    system_args = dict(
        nonbondedMethod=CutoffNonPeriodic,
        nonbondedCutoff=1.0 * unit.nanometer,
        constraints=HBonds,
        soluteDielectric=1.0,
        solventDielectric=78.5,
        implicitSolventKappa=kappa_per_nanometer(ionic_strength_molar) / unit.nanometer,
    )
    system_eq = forcefield.createSystem(topology, **system_args)
    _restraint_force(topology, positions, restraint_kcal, system_eq)

    name, platform = pick_platform(log)
    simulation = Simulation(topology, system_eq,
                            _make_integrator(temperature_k, friction_per_ps, timestep_fs),
                            platform)
    simulation.context.setPositions(positions)

    log(f"md system: {n_atoms} atoms, platform {name}, "
        f"GBn2 implicit solvent, ionic strength {ionic_strength_molar} M")
    log("md minimize")
    simulation.minimizeEnergy(maxIterations=1000)

    equil_steps = max(1, int(round(equil_ps * 1000.0 / timestep_fs)))
    log(f"md equilibrate: {equil_ps:g} ps, backbone restraints {restraint_kcal:g} kcal/mol/A^2")
    simulation.context.setVelocitiesToTemperature(temperature_k * unit.kelvin, seed)
    simulation.step(equil_steps)
    state = simulation.context.getState(getPositions=True, getVelocities=True)

    # Production: a fresh system without the restraints, same coordinates.
    system_prod = forcefield.createSystem(topology, **system_args)
    production = Simulation(topology, system_prod,
                            _make_integrator(temperature_k, friction_per_ps, timestep_fs),
                            platform)
    production.context.setPositions(state.getPositions())
    production.context.setVelocities(state.getVelocities())

    save_every_steps = max(1, int(round(save_every_ps * 1000.0 / timestep_fs)))
    dcd_path = Path(f"{out_prefix}.dcd")
    energy_path = Path(f"{out_prefix}_energy.csv")
    production.reporters.append(DCDReporter(str(dcd_path), save_every_steps))
    production.reporters.append(StateDataReporter(
        str(energy_path), save_every_steps, step=True, time=True,
        potentialEnergy=True, kineticEnergy=True, temperature=True,
        progress=False))

    steps = max(1, int(round(length_ps * 1000.0 / timestep_fs)))
    log(f"md production: {length_ps:g} ps, {steps} steps, "
        f"frames every {save_every_ps:g} ps -> {dcd_path.name}")
    started = time.time()
    production.step(steps)
    wall = time.time() - started
    rate = (steps * timestep_fs / 1000.0) / max(wall, 1e-9)  # ps per second
    log(f"md done: {wall:.0f} s wall, {rate:.1f} ps/s -> {rate * 86.4:.0f} ns/day")

    final_path = Path(f"{out_prefix}_final.pdb")
    final_state = production.context.getState(getPositions=True)
    with open(final_path, "w") as handle:
        PDBFile.writeFile(topology, final_state.getPositions(), handle)

    return {
        "platform": name,
        "n_atoms": n_atoms,
        "production_ps": float(length_ps),
        "equil_ps": float(equil_ps),
        "steps": steps,
        "wall_s": round(wall, 1),
        "ps_per_day_ns": round(rate * 86.4, 1),
        "dcd": str(dcd_path),
        "topology_pdb": str(topology_path),
        "energy_csv": str(energy_path),
        "final_pdb": str(final_path),
    }
