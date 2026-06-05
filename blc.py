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
    return render_named_lambda(parse_blc(bits), "freya")


def blc_to_hvm1(bits):
    return render_hvm1(parse_blc(bits))


def blc_to_hvm3(bits):
    return render_hvm3(parse_blc(bits))


def blc_to_hvm4(bits):
    return render_hvm4(parse_blc(bits))


def blc_to_optiscope_lambda(bits):
    return render_optiscope_lambda(parse_blc(bits))


def render_hvm1(term):
    return render_named_lambda(term, "hvm1")


def render_hvm3(term):
    return render_named_lambda(term, "hvm3")


def render_hvm4(term):
    return render_named_lambda(term, "hvm4")


def render_named_lambda(term, target):
    env = []

    def binder_uses(term, depth=0):
        if isinstance(term, Var):
            return int(term.index == depth)
        if isinstance(term, Abs):
            return binder_uses(term.body, depth + 1)
        return binder_uses(term.func, depth) + binder_uses(term.arg, depth)

    def go(term):
        if isinstance(term, Var):
            if term.index < len(env):
                return env[-term.index - 1]
            return f"f{term.index - len(env)}"

        if isinstance(term, Abs):
            name = f"x{len(env)}"
            clone = target in ("hvm3", "hvm4") and binder_uses(term.body) > 1
            binder = f"&{name}" if clone else name
            env.append(name)
            body = go(term.body)
            env.pop()
            if target == "freya":
                return f"(!{binder} {body})"
            if target == "hvm1":
                return f"@{binder} {body}"
            if target == "hvm3":
                return f"λ{binder} {body}"
            return f"λ{binder}.{body}"

        if target == "hvm4":
            func, args = flatten_app(term)
            return f"{atom(func)}({','.join(go(arg) for arg in args)})"
        return f"({go(term.func)} {go(term.arg)})"

    def flatten_app(term):
        args = []
        while isinstance(term, App):
            args.append(term.arg)
            term = term.func
        args.reverse()
        return term, args

    def atom(term):
        if isinstance(term, Var):
            return go(term)
        return f"({go(term)})"

    return go(term)


def render_optiscope_lambda(term):
    if isinstance(term, Var):
        return str(term.index)
    if isinstance(term, Abs):
        return f"(λ {render_optiscope_lambda(term.body)})"
    return f"({render_optiscope_lambda(term.func)} {render_optiscope_lambda(term.arg)})"


def hvm1_output_to_blc(text):
    return to_blc(parse_hvm_spaced(text.strip()))


def hvm3_output_to_blc(text):
    return hvm1_output_to_blc(first_output_line(text))


def hvm4_output_to_blc(text):
    return to_blc(parse_hvm_call(first_output_line(text)))


def first_output_line(text):
    return next(line.strip() for line in text.splitlines() if line.strip())


def parse_hvm_spaced(text):
    pos = 0
    env = []

    def space():
        nonlocal pos
        while pos < len(text) and text[pos].isspace():
            pos += 1

    def name():
        nonlocal pos
        space()
        start = pos
        while (
            pos < len(text)
            and not text[pos].isspace()
            and text[pos] not in "(){};"
        ):
            pos += 1
        return text[start:pos]

    def term():
        nonlocal pos
        space()
        if text[pos] == "(":
            pos += 1
            app = term()
            while True:
                space()
                if text[pos] == ")":
                    pos += 1
                    return app
                app = App(app, term())
        if text[pos] in "@λ":
            pos += 1
            var = name().lstrip("&")
            env.append(var)
            body = term()
            env.pop()
            return Abs(body)
        var = name()
        return Var(bound_index(env, var))

    return term()


def parse_hvm_call(text):
    pos = 0
    env = []

    def space():
        nonlocal pos
        while pos < len(text) and text[pos].isspace():
            pos += 1

    def name():
        nonlocal pos
        space()
        start = pos
        while (
            pos < len(text)
            and not text[pos].isspace()
            and text[pos] not in "().,{};"
        ):
            pos += 1
        return text[start:pos]

    def term():
        nonlocal pos
        space()
        if text[pos] == "λ":
            pos += 1
            var = name().lstrip("&")
            space()
            if text[pos] == ".":
                pos += 1
            env.append(var)
            body = term()
            env.pop()
            return Abs(body)

        app = atom()
        space()
        while pos < len(text) and text[pos] == "(":
            pos += 1
            while True:
                app = App(app, term())
                space()
                if text[pos] == ")":
                    pos += 1
                    break
                if text[pos] == ",":
                    pos += 1
            space()
        return app

    def atom():
        nonlocal pos
        space()
        if text[pos] == "(":
            pos += 1
            value = term()
            space()
            pos += 1
            return value
        var = name()
        return Var(bound_index(env, var))

    return term()


def bound_index(env, name):
    return list(reversed(env)).index(name)


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
