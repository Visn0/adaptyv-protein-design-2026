#!/usr/bin/env python3
"""Graduated CUDA test — the mandatory gate before any CUDA work on this host.

Hard rule (after the crash series of 2026-10-25..27): do not start a fold on a
fresh boot without this test passing. Run with the chai venv python:

    ~/.venvs/chai/bin/python cuda-graduated-test.py

T-A: minimal CUDA init. T-B: 1 GB allocation + 10x 4096^2 matmul (the shape
class that surfaced driver instability in the 0xD1 family). Both must print OK.
"""
import time

import torch

print('torch', torch.__version__, '| cuda available:', torch.cuda.is_available())
assert torch.cuda.is_available(), 'CUDA not available'

t0 = time.time()
x = torch.zeros(1024, device='cuda')
s = (x + 1).sum().item()
print(f'T-A minimal init: OK in {time.time() - t0:.1f}s (sum={s})')

t0 = time.time()
a = torch.randn(4096, 4096, device='cuda')
b = torch.randn(4096, 4096, device='cuda')
for _ in range(10):
    c = a @ b
torch.cuda.synchronize()
print(f'T-B 1 GB alloc + 10x 4096^2 matmul: OK in {time.time() - t0:.1f}s (norm={c.norm().item():.1f})')
del a, b, c, x
torch.cuda.empty_cache()
print('CUDA_GRADUATED_TEST_PASS')
