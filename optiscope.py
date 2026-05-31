#!/bin/env python3

import multiprocessing
import os
import subprocess

from blc import App, Abs, Var, blc_to_optiscope_lambda, parse_blc, read_tests


GROUP = 100
CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
TESTS = read_tests()


def symbolify(n):
    base = len(CHARS)
    symbol = "_"
    while n:
        symbol += CHARS[n % base]
        n //= base
    return symbol


def c_function(bits, func_id):
    term = parse_blc(bits)
    used = []
    env = []
    next_symbol = 1

    def go(term):
        nonlocal next_symbol

        if isinstance(term, Var):
            return f"var({env[-term.index - 1]})"

        if isinstance(term, Abs):
            symbol = symbolify(next_symbol)
            next_symbol += 1
            used.append(symbol)
            env.append(symbol)
            body = go(term.body)
            env.pop()
            return f"lambda({symbol}, {body})"

        if isinstance(term, App):
            return f"apply({go(term.func)}, {go(term.arg)})"

        raise TypeError(term)

    body = go(term)
    decls = ", ".join(f"*{symbol}" for symbol in used)
    declaration = f"  struct lambda_term {decls};\n" if decls else ""

    return f"""
static struct lambda_term *
func{func_id}(void) {{
{declaration}  return {body};
}}
"""


def c_file(functions, tests):
    return f"""
#include <sys/wait.h>
#include <unistd.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>

#define TIMEOUT_TEST(test_code) do {{ \\
    pid_t pid = fork(); \\
    if (pid == 0) {{ \\
        test_code; \\
        exit(0); \\
    }} else if (pid > 0) {{ \\
        int status; \\
        pid_t result = waitpid(pid, &status, WNOHANG); \\
        \\
        for (int i = 0; i < 50 && result == 0; i++) {{ \\
            usleep(100000); \\
            result = waitpid(pid, &status, WNOHANG); \\
        }} \\
        \\
        if (result == 0) {{ \\
            printf("Timeout!\\n"); \\
            fflush(stdout); \\
            kill(pid, SIGKILL); \\
            waitpid(pid, &status, 0); \\
        }} else if (WIFEXITED(status) && WEXITSTATUS(status) == 0) {{ \\
            printf("Passed!\\n"); \\
            fflush(stdout); \\
        }} else {{ \\
            printf("Failed!\\n"); \\
            fflush(stdout); \\
        }} \\
    }} else {{ \\
        perror("Failed!"); \\
    }} \\
}} while(0)

#define OPTISCOPE_TESTS_NO_MAIN
#undef _DEFAULT_SOURCE

#include "optiscope/tests.c"

{functions}

int main(void) {{
  {tests}
}}
"""


def comment(text):
    return text.replace("*/", "* /")


def run_range(start, end):
    functions = []
    cases = []

    for func_id, test in enumerate(TESTS[start:end], start):
        cases.append(
            f'TIMEOUT_TEST(TEST_CASE(func{func_id}, "{blc_to_optiscope_lambda(test.normal)}"));'
        )
        functions.append(f"// {comment(test.label)}\n{c_function(test.source, func_id)}")

    source = f"optiscopeTests{start}.c"
    binary = f"optiscopeTests{start}.out"

    with open(source, "w", encoding="utf-8") as file:
        file.write(c_file("\n".join(functions), "\n".join(cases)))

    subprocess.run(
        ["cc", source, "optiscope/optiscope.c", "-Ioptiscope", "-o", binary],
        check=True,
    )
    out = subprocess.check_output([f"./{binary}"], stderr=subprocess.STDOUT).decode()

    passed = out.count("Good")
    timeout = out.count("Timeout")
    failed = out.count("Failed")

    print(
        f"Group {start}-{end}: passed={passed}, timeout={timeout}, failed={failed}",
        flush=True,
    )

    for path in (source, binary):
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
    return passed, timeout, failed


def main():
    ranges = [(start, min(start + GROUP, len(TESTS))) for start in range(0, len(TESTS), GROUP)]

    with multiprocessing.Pool(processes=4) as pool:
        results = pool.starmap(run_range, ranges)

    print("passed:", sum(result[0] for result in results))
    print("timeout:", sum(result[1] for result in results))
    print("failed:", sum(result[2] for result in results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
