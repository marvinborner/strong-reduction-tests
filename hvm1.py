#!/bin/env python3

import os
import subprocess
import tempfile

from blc import (
    blc_to_hvm1,
    ensure_recursion_limit,
    eta_equivalent,
    hvm1_output_to_blc,
    read_tests,
)

TIMEOUT = 5
HVM1_DIR = os.path.abspath("hvm1")
BINARY = os.path.join(HVM1_DIR, "target", "debug", "hvm1")


subprocess.run(["cargo", "build", "--quiet"], cwd=HVM1_DIR, check=True)


def reduce(term):
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".hvm", delete=False
        ) as file:
            file.write(f"Main = {blc_to_hvm1(term)}\n")
            tmp = file.name

        result = subprocess.run(
            [BINARY, "run", "-f", tmp],
            cwd=HVM1_DIR,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )
    finally:
        if tmp is not None:
            os.unlink(tmp)

    if result.returncode != 0:
        error = result.stderr.strip() or f"exit code {result.returncode}"
        raise RuntimeError(error)

    return hvm1_output_to_blc(result.stdout.strip())


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
