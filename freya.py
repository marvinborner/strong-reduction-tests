#!/bin/env python3

import os
import subprocess
import tempfile

from blc import blc_to_freya, ensure_recursion_limit, read_tests


TIMEOUT = 5
BINARY = os.path.abspath("opteval/target/release/opteval")


def run(expr):
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".lc", delete=False) as file:
            file.write(expr)
            tmp = file.name

        result = subprocess.run(
            [BINARY, "-f", tmp],
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
        )
        return result.stdout.strip()
    finally:
        if tmp is not None:
            os.unlink(tmp)


def main():
    ensure_recursion_limit()
    passed = timeout = failed = 0

    for test in read_tests():
        expected = blc_to_freya(test.normal)

        try:
            actual = run(blc_to_freya(test.source))
        except subprocess.TimeoutExpired:
            timeout += 1
            print(f"TIMEOUT {test.label}")
            continue

        if actual == expected:
            passed += 1
        else:
            failed += 1
            print(f"FAIL {test.label}: got {actual}, expected {expected}")

    print(f"passed: {passed}")
    print(f"timeout: {timeout}")
    print(f"failed: {failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
