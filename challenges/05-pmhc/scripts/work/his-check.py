#!/usr/bin/env python3
"""Check histidine ring-nitrogen distances to the D6 carboxylate in a fold."""

from __future__ import annotations

import sys

import gemmi


def main() -> int:
    for path in sys.argv[1:]:
        st = gemmi.read_structure(path)[0]
        b = st.find_chain("D")
        pep = st.find_chain("C")
        d6 = [a for rr in pep if rr.seqid.num == 6 for a in rr
              if a.name in ("OD1", "OD2")]
        print(f"== {path.split('/')[-1]}")
        for rr in b:
            if rr.name != "HIS":
                continue
            for a in rr:
                if a.name in ("ND1", "NE2"):
                    d = min(a.pos.dist(x.pos) for x in d6)
                    print(f"   HIS{rr.seqid.num}:{a.name} -> D6 {d:.2f} A")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
