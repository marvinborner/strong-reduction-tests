#!/bin/env python3

import os
import subprocess
import tempfile

from blc import (
    blc_to_hvm3,
    ensure_recursion_limit,
    eta_equivalent,
    hvm3_output_to_blc,
    read_tests,
)

TIMEOUT = 5
HVM3_DIR = os.path.abspath("hvm3")


subprocess.run(["cabal", "build"], cwd=HVM3_DIR, check=True)


def binary():
    result = subprocess.run(
        ["cabal", "list-bin", "hvm"],
        cwd=HVM3_DIR,
        capture_output=True,
        text=True,
        check=True,
    )
    for line in reversed(result.stdout.splitlines()):
        path = line.strip()
        if path and os.path.exists(path):
            return path
    raise RuntimeError("could not locate HVM3 executable")


def reduce(binary, term):
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".hvm", delete=False
        ) as file:
            file.write(f"@main = {blc_to_hvm3(term)}\n")
            tmp = file.name

        result = subprocess.run(
            [binary, "run", tmp, "-C"],
            cwd=HVM3_DIR,
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

    return hvm3_output_to_blc(result.stdout)


ensure_recursion_limit()
hvm3 = binary()

passed = 0
failed = 0
timeouted = 0

for test in read_tests("tests_eal"):
    try:
        normal = reduce(hvm3, test.source)
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
