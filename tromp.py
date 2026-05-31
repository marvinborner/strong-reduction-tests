#!/bin/env python3

import subprocess

from blc import eta_equivalent, read_tests, tromp_output_to_blc


TIMEOUT = 5


def compile_normalizer():
    subprocess.run(["cc", "-O2", "nf.c"], check=True)


def reduce(term):
    proc = subprocess.Popen(
        ["./a.out", "-b"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    try:
        stdout, _ = proc.communicate(term.encode("utf-8"), timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        proc.kill()
        raise TimeoutError

    if proc.returncode != 0:
        raise RuntimeError(proc.returncode)

    return tromp_output_to_blc(stdout.decode("utf-8").strip())


def main():
    compile_normalizer()

    passed = []
    timeout = []
    failed = []

    for test in read_tests():
        try:
            normal = reduce(test.source)
            if eta_equivalent(normal, test.normal):
                passed.append(test.label)
            else:
                print(f"failed! Got {normal}, expected {test.normal}")
                failed.append(test.label)
        except TimeoutError:
            print("timeout!")
            timeout.append(test.label)
        except Exception as exc:
            print(f"exception! {exc}")
            failed.append(test.label)

    print("passed:", len(passed))
    print("timeout:", len(timeout))
    print("failed:", len(failed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
