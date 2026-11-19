"""Experiment machinery: specs, the runner, the worker, device detection.

An experiment is one YAML spec (challenges/<c>/experiments/*.yaml) that names a
pipeline from tools.pipelines and the stages + params to run. Every execution
creates a fresh run directory under challenges/<c>/runs/ containing run.log,
status.json, summary.json and artifacts/. Runs are isolated, so the same
experiment can be re-run or several can run in parallel without clobbering.
"""
