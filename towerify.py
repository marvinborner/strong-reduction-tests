#!/usr/bin/env python3
import sys
from pathlib import Path
from blc import BlcError, read_tests

CHURCH_TRUE = "0000110"  # λt.λf.t
CHURCH_FALSE = "000010"  # λt.λf.f
LIST_NIL = "000010"  # λc.λn.n
CONS_PREFIX = "00010110"  # λc. ((1 <bool>) <tail>)


def meta(bits):
    out = []
    for bit in bits:
        out.append(CONS_PREFIX)
        out.append(CHURCH_TRUE if bit == "0" else CHURCH_FALSE)
    out.append(LIST_NIL)
    return "".join(out)


def tower(term, height, uni):
    current = term
    for _ in range(height):
        current = "01" + uni + meta("00" + current)
    return current


if len(sys.argv) != 2 or not sys.argv[1].isdigit():
    print(f"usage: {sys.argv[0]} HEIGHT", file=sys.stderr)
    sys.exit(1)

height = int(sys.argv[1])

uni = Path("uni.blc").read_text(encoding="utf-8")
for test in read_tests("tests"):
    source = tower(test.source, height, uni)
    print(f"{test.label}: {source} - {test.normal}")
