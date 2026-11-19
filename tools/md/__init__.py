"""All-atom molecular dynamics helpers (OpenMM).

prepare   text and geometry work. Runs on the CPU in seconds.
simulate  one OpenMM run with implicit solvent (GBn2).
analyze   trajectory metrics (mdtraj) and the movie frame files.
player    the interactive player page (cartoon / surface, both pH states).

The stage driver lives in tools/pipelines/md.py.
"""
