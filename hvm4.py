#!/bin/env python3

import os
import subprocess
import tempfile

from blc import (
    blc_to_hvm4,
    ensure_recursion_limit,
    eta_equivalent,
    hvm4_output_to_blc,
    read_tests,
)

TIMEOUT = 5
HVM4_DIR = os.path.abspath("hvm4")
BINARY = os.path.join(HVM4_DIR, "src", "hvm")


subprocess.run(
    ["clang", "-O2", "-o", "src/hvm", "src/hvm.c"],
    cwd=HVM4_DIR,
    check=True,
)


def reduce(term):
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".hvm", delete=False
        ) as file:
            file.write(f"@main = {blc_to_hvm4(term)}\n")
            tmp = file.name

        result = subprocess.run(
            [BINARY, tmp, "-C"],
            cwd=HVM4_DIR,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )
    finally:
        if tmp is not None:
            os.unlink(tmp)

    if result.returncode != 0:
        error = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(error or f"exit code {result.returncode}")

    return hvm4_output_to_blc(result.stdout)


ensure_recursion_limit()

passed = 0
failed = 0
timeouted = 0

for test in read_tests("tests_eal"):
    try:
        normal = reduce(test.source)
    except subprocess.TimeoutExpired:
        timeouted += 1
        print(f"TIMEOUT {test.label}")
        continue
    except Exception as exc:
        failed += 1
        print(f"FAIL {test.label}: {exc}")
        continue

    if normal == test.normal:
        passed += 1
    else:
        failed += 1
        print(f"FAIL {test.label}: got {normal}, expected {test.normal}")

print(f"passed: {passed}")
print(f"failed: {failed}")
print(f"timeouted: {timeouted}")
