"""Pipeline registry: maps spec `pipeline:` keys to callables.

A pipeline is `run(ctx: tools.common.RunContext) -> summary dict`. The summary
is written to summary.json and drives the HTML report (tables, charts, viewer
hints). Raise tools.common.WaitingInputsError when a stage needs artifacts
that are not present yet (the run is marked `waiting_inputs`, not `failed`).
"""
from tools.pipelines import fold, md, screen

PIPELINES = {
    "fold": fold.run,
    "md": md.run,
    "screen": screen.run,
}
