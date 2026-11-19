"""Experiment specs: one YAML file per experiment under challenges/<c>/experiments/.

Spec format (all relative paths resolve against the challenge directory):

    name: c2-fold-w1-gpu
    challenge: 02-tnfa
    pipeline: fold               # tools/pipelines registry key
    description: "One design co-folded against the TNF-alpha trimer, IPSAE-scored."
    resources: cpu               # cpu | gpu | auto
    requires_network: false
    stages: [import]             # subset of the pipeline's stages
    params:
      source: data/boltz2/w1-gpu-s42
      binder_chain: A
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from tools import common

REQUIRED_KEYS = ("name", "challenge", "pipeline")


@dataclass
class Spec:
    path: Path
    name: str
    challenge: str
    pipeline: str
    description: str = ""
    resources: str = "cpu"
    reference: bool = False
    requires_network: bool = False
    stages: list = field(default_factory=list)
    params: dict = field(default_factory=dict)

    @property
    def challenge_dir(self) -> Path:
        return common.CHALLENGES_DIR / self.challenge

    @property
    def runs_root(self) -> Path:
        return self.challenge_dir / "runs"


def load_spec(path: str | Path) -> Spec:
    path = Path(path)
    data = yaml.safe_load(path.read_text()) or {}
    missing = [key for key in REQUIRED_KEYS if key not in data]
    if missing:
        raise ValueError(f"{path}: missing required keys {missing}")
    return Spec(
        path=path,
        name=str(data["name"]),
        challenge=str(data["challenge"]),
        pipeline=str(data["pipeline"]),
        description=str(data.get("description", "")),
        resources=str(data.get("resources", "cpu")),
        reference=bool(data.get("reference", False)),
        requires_network=bool(data.get("requires_network", False)),
        stages=list(data.get("stages", [])),
        params=dict(data.get("params", {})),
    )


def discover() -> list[Spec]:
    """All experiment specs in the repo, sorted by challenge then name."""
    specs = []
    for path in sorted(common.CHALLENGES_DIR.glob("*/experiments/*.yaml")):
        try:
            specs.append(load_spec(path))
        except Exception as exc:  # keep listing usable even with a broken spec
            print(f"warning: skipping {path}: {exc}")
    return specs


def specs_by_name(challenge: str | None = None) -> dict[str, Spec]:
    """name -> Spec, optionally limited to one challenge (one glob, not a scan)."""
    if challenge:
        paths = sorted((common.CHALLENGES_DIR / challenge / "experiments").glob("*.yaml"))
        specs = []
        for path in paths:
            try:
                specs.append(load_spec(path))
            except Exception as exc:
                print(f"warning: skipping {path}: {exc}")
        return {spec.name: spec for spec in specs}
    return {spec.name: spec for spec in discover()}
