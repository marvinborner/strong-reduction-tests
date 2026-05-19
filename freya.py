#!/bin/env python3

import os
import subprocess
import re
import sys
import tempfile

TIMEOUT = 5
BINARY = os.path.abspath("opteval/target/release/opteval")
TESTS = open("tests").readlines()

sys.setrecursionlimit(100000)


def parse_blc(s, i=0):
    if s[i] == "0" and s[i + 1] == "0":
        body, j = parse_blc(s, i + 2)
        return ("abs", body), j
    elif s[i] == "0" and s[i + 1] == "1":
        f, j = parse_blc(s, i + 2)
        a, k = parse_blc(s, j)
        return ("app", f, a), k
    else:
        cnt = 0
        pos = i
        while pos < len(s) and s[pos] == "1":
            cnt += 1
            pos += 1
        return ("var", cnt - 1), pos + 1


def to_freya(tree, depth=0):
    if tree[0] == "abs":
        name = f"x{depth}"
        body = to_freya(tree[1], depth + 1)
        return f"(!{name} {body})"
    elif tree[0] == "app":
        f = to_freya(tree[1], depth)
        a = to_freya(tree[2], depth)
        return f"({f} {a})"
    else:
        idx = tree[1]
        return f"x{depth - idx - 1}"


passed, timeout, failed = 0, 0, 0

for line in TESTS:
    line = line.strip()
    bruijn, tests = line.split(": ", 1)
    left_blc, right_blc = tests.split(" - ")

    left_tree, _ = parse_blc(left_blc)
    right_tree, _ = parse_blc(right_blc)
    expected = to_freya(right_tree)

    expr = to_freya(left_tree)
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".lc", delete=False
        ) as f:
            f.write(expr)
            tmp = f.name
        result = subprocess.run(
            [BINARY, "-f", tmp],
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )
        os.unlink(tmp)
        actual = result.stdout.strip()
        if actual == expected:
            passed += 1
        else:
            failed += 1
            err = result.stderr.strip()
            print(f"FAIL {bruijn}: got {actual}, expected {expected}")
            if err:
                print(f"  stderr: {err}")
    except subprocess.TimeoutExpired:
        os.unlink(tmp)
        timeout += 1
        print(f"TIMEOUT {bruijn}")

print(f"passed: {passed}")
print(f"timeout: {timeout}")
print(f"failed: {failed}")
