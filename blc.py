import re
import sys
from pathlib import Path

TEST_RE = re.compile(
    r"^(?P<label>.*):\s*(?P<source>[01]+)\s+-\s*(?P<normal>[01]+)\s*$"
)


class Test:
    def __init__(self, label, source, normal):
        self.label = label
        self.source = source
        self.normal = normal


class Var:
    def __init__(self, index):
        self.index = index


class Abs:
    def __init__(self, body):
        self.body = body


class App:
    def __init__(self, func, arg):
        self.func = func
        self.arg = arg


class BlcError(ValueError):
    pass


class Parser:
    def __init__(self, bits):
        self.bits = bits
        self.pos = 0

    def parse(self):
        term = self.term()
        if self.pos != len(self.bits):
            raise BlcError(f"trailing bits at offset {self.pos}")
        return term

    def term(self):
        if self.pos >= len(self.bits):
            raise BlcError("unexpected end of input")

        tag = self.bits[self.pos : self.pos + 2]
        if tag == "00":
            self.pos += 2
            return Abs(self.term())
        if tag == "01":
            self.pos += 2
            return App(self.term(), self.term())
        return Var(self.var())

    def var(self):
        start = self.pos
        while self.pos < len(self.bits) and self.bits[self.pos] == "1":
            self.pos += 1

        if self.pos == start:
            raise BlcError(f"invalid tag at offset {start}")
        if self.pos >= len(self.bits) or self.bits[self.pos] != "0":
            raise BlcError(f"unterminated variable at offset {start}")

        index = self.pos - start - 1
        self.pos += 1
        return index


def ensure_recursion_limit(limit=1_000_000):
    sys.setrecursionlimit(max(sys.getrecursionlimit(), limit))


def parse_blc(bits):
    return Parser(bits).parse()


def to_blc(term):
    if isinstance(term, Var):
        return "1" * (term.index + 1) + "0"
    if isinstance(term, Abs):
        return "00" + to_blc(term.body)
    return "01" + to_blc(term.func) + to_blc(term.arg)


def tromp_output_to_blc(term):
    bits = []
    for char in term:
        if char == "\\":
            bits.append("00")
        elif char == "`":
            bits.append("01")
        else:
            bits.append("1" * (ord(char) - ord("0") + 1) + "0")
    return "".join(bits)


def read_test_line(line):
    line = line.strip()
    if not line:
        return None

    match = TEST_RE.match(line)
    if match is None:
        raise BlcError(f"bad test line: {line[:120]!r}")

    return Test(
        match.group("label"),
        match.group("source"),
        match.group("normal"),
    )


def read_tests(path="tests"):
    tests = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            try:
                test = read_test_line(line)
            except Exception as exc:
                raise BlcError(f"{path}:{line_no}: {exc}") from exc
            if test is not None:
                tests.append(test)
    return tests


def blc_to_freya(bits):
    return render_freya(parse_blc(bits))


def blc_to_optiscope_lambda(bits):
    return render_optiscope_lambda(parse_blc(bits))


def render_freya(term):
    env = []

    def go(term):
        if isinstance(term, Var):
            if term.index < len(env):
                return env[-term.index - 1]
            return f"f{term.index - len(env)}"

        if isinstance(term, Abs):
            name = f"x{len(env)}"
            env.append(name)
            body = go(term.body)
            env.pop()
            return f"(!{name} {body})"

        return f"({go(term.func)} {go(term.arg)})"

    return go(term)


def render_optiscope_lambda(term):
    if isinstance(term, Var):
        return str(term.index)
    if isinstance(term, Abs):
        return f"(λ {render_optiscope_lambda(term.body)})"
    return f"({render_optiscope_lambda(term.func)} {render_optiscope_lambda(term.arg)})"


def eta_equivalent(a, b):
    ensure_recursion_limit()
    return to_blc(eta_normal_form(parse_blc(a))) == to_blc(
        eta_normal_form(parse_blc(b))
    )


def eta_normal_form(term):
    if isinstance(term, Var):
        return term

    if isinstance(term, App):
        return App(eta_normal_form(term.func), eta_normal_form(term.arg))

    body = eta_normal_form(term.body)
    if (
        isinstance(body, App)
        and isinstance(body.arg, Var)
        and body.arg.index == 0
        and not contains_bound_var(body.func)
    ):
        return drop_binder(body.func)
    return Abs(body)


def contains_bound_var(term, depth=0):
    if isinstance(term, Var):
        return term.index == depth
    if isinstance(term, Abs):
        return contains_bound_var(term.body, depth + 1)
    return contains_bound_var(term.func, depth) or contains_bound_var(
        term.arg, depth
    )


def drop_binder(term, depth=0):
    if isinstance(term, Var):
        return Var(term.index - (term.index > depth))
    if isinstance(term, Abs):
        return Abs(drop_binder(term.body, depth + 1))
    return App(drop_binder(term.func, depth), drop_binder(term.arg, depth))
