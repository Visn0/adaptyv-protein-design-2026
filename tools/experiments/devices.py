"""What compute does this machine offer? (cpu / apple-mps / cuda)

Every experiment declares `resources:` in its spec:

    cpu     always runs here
    gpu     wants an accelerator. On a machine without CUDA it resolves to the
            best fallback (MPS, then CPU) and says so — the same spec runs on
            an Nvidia PC (CUDA) and on this Mac (MPS/CPU) without edits.
    auto    picks the best device the machine offers

Resolution order: cuda -> mps -> cpu. Override with PDT_DEVICE (cuda|mps|cpu).

The heavy generators (RFdiffusion, BindCraft, AlphaFold2) are CUDA-bound and
run externally (see the challenge notes). Local torch stages (e.g. ProteinMPNN
inference) call plan_for() — `make torch` installs torch, then they pick the
GPU by themselves.
"""
from __future__ import annotations

import os
import platform
import subprocess
import sys

RESOLUTION_ORDER = ("cuda", "mps", "cpu")


def torch_info() -> dict:
    try:
        import torch  # noqa: PLC0415

        mps = bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available())
        cuda = bool(torch.cuda.is_available())
        return {"torch": torch.__version__, "mps": mps, "cuda": cuda}
    except Exception as exc:  # torch not installed or unusable
        return {"torch": None, "mps": None, "cuda": None, "torch_error": type(exc).__name__}


def cpu_brand() -> str:
    if platform.system() == "Darwin":
        try:
            out = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True,
            )
            if out.stdout.strip():
                return out.stdout.strip()
        except Exception:
            pass
    return platform.processor() or platform.machine() or "unknown-cpu"


def detect() -> dict:
    info = {
        "cpu": cpu_brand(),
        "cpu_count": os.cpu_count(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
    }
    info.update(torch_info())
    if info.get("mps"):
        info["recommended"] = "mps"
    elif info.get("cuda"):
        info["recommended"] = "cuda"
    else:
        info["recommended"] = "cpu"
    return info


def plan_for(resources: str = "cpu", override: str | None = None) -> dict:
    """Resolve a spec's `resources` request against this machine.

    Returns requested / resolved / fallback / reason / available.
    `fallback` is True only when a spec asked for `gpu` and no CUDA exists:
    the run continues on MPS or CPU with a note in the log.
    """
    info = detect()
    available = {"cuda": bool(info.get("cuda")), "mps": bool(info.get("mps")), "cpu": True}
    if override is None:
        override = (os.environ.get("PDT_DEVICE") or "auto").strip().lower()
    requested = str(resources or "cpu").strip().lower()

    if override in ("cuda", "mps", "cpu"):
        resolved = override
        reason = f"PDT_DEVICE={override}"
    elif requested == "cpu":
        resolved = "cpu"
        reason = "the spec asks for cpu"
    else:  # gpu / auto -> best device this machine offers
        resolved = next(name for name in RESOLUTION_ORDER if available[name])
        if resolved == "cuda":
            reason = "CUDA is available"
        elif resolved == "mps":
            reason = "no CUDA here; using the Apple GPU (MPS)"
        else:
            reason = "no CUDA here; using the CPU"
    fallback = requested == "gpu" and resolved != "cuda" and override not in ("cuda", "mps", "cpu")
    return {
        "requested": requested,
        "resolved": resolved,
        "fallback": bool(fallback),
        "reason": reason,
        "available": available,
    }


def describe() -> str:
    info = detect()
    plan = plan_for("gpu")
    lines = [
        f"cpu         : {info['cpu']} ({info['cpu_count']} cores)",
        f"platform    : {info['platform']}",
        f"python      : {info['python']}",
        f"torch       : {info['torch'] or 'not installed'}"
        + (f" ({info.get('torch_error')})" if info.get("torch_error") else ""),
        f"mps (Apple) : {info['mps'] if info['mps'] is not None else 'unknown (torch not installed)'}",
        f"cuda        : {info['cuda'] if info['cuda'] is not None else 'unknown (torch not installed)'}",
        f"recommended : {info['recommended']}",
        "",
        f"resources: gpu  -> resolves to '{plan['resolved']}'"
        + ("  (fallback: no CUDA on this machine)" if plan["fallback"] else ""),
        "override        : PDT_DEVICE=cuda|mps|cpu|auto",
    ]
    if info["torch"] is None:
        lines += [
            "",
            "note: torch is not installed. The current stages are CPU (PROPKA, geometry).",
            "      `make torch` installs it — then MPS/CUDA stages pick the GPU themselves,",
            "      and the SAME specs also run on an Nvidia PC with CUDA. RFdiffusion/",
            "      BindCraft/AlphaFold2 stay external (CUDA); their specs say so in the",
            "      steps tree, with the fallback path for this Mac.",
        ]
    return "\n".join(lines)
