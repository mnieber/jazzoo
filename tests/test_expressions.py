import pytest

from jazzoo import evaluate, parse_module
from jazzoo.runtime.utils.test_utils import save_fixture


def test_all_values_are_strings():
    """All values are strings. There are no integers."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_values_are_strings.jaz
        🐭.number = "123"

        go():
            🐆.retval = 🐭.number
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "123"

    """Unquoted values are treated as bare strings, so quoting is optional."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bare_strings.jaz
        🐭.bare = hello
        🐭.quoted = "hello"
        🐭.also-bare = 🐭.bare\\.com

        bare-fn():
            🐆.x = hello
            🐆.retval = 🐆.x

        module-level-fn():
            🐆.retval = "🐭.bare/🐭.quoted"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.bare-fn()") == "hello"
        # A dot continues the name into a structured lookup, so a literal dotted
        # suffix needs the `\` that ends the name.
        assert evaluate(root_module, "🐭.also-bare") == "hello.com"
        assert evaluate(root_module, "🐭.module-level-fn()") == "hello/hello"


def test_a_ternary_selects_on_string_equality():
    """Only string equality (==) is supported as a condition."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_ternary_equality.jaz
        🐐.log-level = "high"

        matches():
            🐆.dry-run = "--dry-run" if 🐐.log-level == "high" else ""
            🐆.retval = "[🐆.dry-run]"

        does-not-match():
            🐆.dry-run = "--dry-run" if 🐐.log-level == "low" else ""
            🐆.retval = "[🐆.dry-run]"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.matches()") == "[--dry-run]"
        assert evaluate(root_module, "🐭.does-not-match()") == "[]"


def test_a_ternary_tests_bare_variable_truthiness():
    """Besides string equality, a condition may be a bare variable, tested for
    truthiness."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_ternary_truthiness.jaz
        🐭.enabled = "yes"
        🐭.disabled = ""

        truthy():
            🐆.retval = "on" if 🐭.enabled else "off"

        falsy():
            🐆.retval = "on" if 🐭.disabled else "off"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.truthy()") == "on"
        assert evaluate(root_module, "🐭.falsy()") == "off"


def test_falsy_strings_are_the_env_var_style_flags():
    """A string value is falsy if its lowercased form is in ["0", "false", "no", ""].
    All other strings are truthy, which allows natural use of env-var-style flags."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_falsy_values.jaz
        check(flag):
            🐆.retval = "truthy" if 🐆.flag else "falsy"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        for falsy in ["0", "false", "no", ""]:
            assert evaluate(root_module, f'🐭.check(flag="{falsy}")') == "falsy"

        # Lowercasing means the capitalized spellings are falsy too.
        for falsy in ["False", "FALSE", "No", "NO"]:
            assert evaluate(root_module, f'🐭.check(flag="{falsy}")') == "falsy"

        # Everything else is truthy - including strings that merely contain a
        # falsy word, and "1"/"true"/"yes".
        for truthy in ["1", "true", "yes", "off", "none", "0.0", " ", "false-ish"]:
            assert evaluate(root_module, f'🐭.check(flag="{truthy}")') == "truthy"


def test_ternaries_chain_right_associatively():
    """Chaining is right-associative: `A if C1 else B if C2 else C` groups as
    `A if C1 else (B if C2 else C)`."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_ternary_chain.jaz
        classify(level):
            🐆.retval = "a" if 🐆.level == "high" else "b" if 🐆.level == "low" else ""
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, '🐭.classify(level="high")') == "a"
        assert evaluate(root_module, '🐭.classify(level="low")') == "b"
        assert evaluate(root_module, '🐭.classify(level="medium")') == ""


def test_the_path_operator_joins_two_values():
    """The `/` operator joins two string values as path segments, producing a new
    string."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_path_join.jaz
        🐭.base = "/data"

        go():
            🐆.retval = 🐭.base / "build/output"

        from-a-system-variable():
            🐆.retval = ⚙️.module.dirname / "build"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "/data/build/output"
        assert evaluate(root_module, "🐭.from-a-system-variable()").endswith("/build")


def test_a_path_join_is_a_pure_string_join():
    """Path joins are a pure string join - `..`, symlinks and redundant separators are
    left untouched. Joining never canonicalizes on its own."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_path_is_textual.jaz
        dot-dot():
            🐆.retval = "/data/sub" / "../config.json"

        redundant-separators():
            🐆.retval = "/data/" / "/config.json"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # `..` survives the join rather than being resolved away.
        assert evaluate(root_module, "🐭.dot-dot()") == "/data/sub/../config.json"
        assert (
            evaluate(root_module, "🐭.redundant-separators()") == "/data//config.json"
        )


def test_path_joins_chain_left_associatively():
    """Path expressions can be chained: `a / b / c` is left-associative."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_path_chain.jaz
        go():
            🐆.retval = "/data" / "sub" / "input.json"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "/data/sub/input.json"


def test_a_function_call_can_be_a_path_segment():
    """A path expression may join the return value of a function call."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_path_from_call.jaz
        [private]
        _get_base_path():
            #!/usr/bin/env bash
            echo "/data/base"

        go():
            🐆.retval = 🐭._get_base_path() / "config.json"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "/data/base/config.json"


def test_abs_is_the_only_way_to_canonicalize():
    """The only way to canonicalize a path is to pipe it to ⚙️.abs."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_abs.jaz
        go():
            🐆.retval = "/data/sub/../config.json" | ⚙️.abs
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "/data/config.json"


def test_abs_applies_after_the_whole_join_or_to_the_prefix_only():
    """`a / b | ⚙️.abs` resolves the whole join; `a | ⚙️.abs / b` resolves the prefix
    and then joins the rest as a raw string."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_abs_precedence.jaz
        [private]
        _get_base_path():
            #!/usr/bin/env bash
            echo "/data/base/sub"

        whole-join():
            🐆.retval = 🐭._get_base_path() / "../config.json" | ⚙️.abs

        prefix-only():
            🐆.retval = 🐭._get_base_path() | ⚙️.abs / "../config.json"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.whole-join()") == "/data/base/config.json"
        assert (
            evaluate(root_module, "🐭.prefix-only()") == "/data/base/sub/../config.json"
        )


def test_the_path_pipe_operators():
    """⚙️.basename, ⚙️.dirname, ⚙️.ext and ⚙️.stem each yield one part of a path."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_path_operators.jaz
        🐭.path = "/data/sub/input.json"

        basename():
            🐆.retval = 🐭.path | ⚙️.basename

        dirname():
            🐆.retval = 🐭.path | ⚙️.dirname

        ext():
            🐆.retval = 🐭.path | ⚙️.ext

        stem():
            🐆.retval = 🐭.path | ⚙️.stem
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.basename()") == "input.json"
        assert evaluate(root_module, "🐭.dirname()") == "/data/sub"
        assert evaluate(root_module, "🐭.ext()") == ".json"
        assert evaluate(root_module, "🐭.stem()") == "/data/sub/input"


def test_pipe_operators_chain_with_path_expressions():
    """Pipe operators and path joins combine in a single expression."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_operators_chained.jaz
        🐭.path = "/data/sub/input.json"

        go():
            🐆.retval = 🐭.path | ⚙️.basename | ⚙️.stem

        rebuild():
            🐆.retval = 🐭.path | ⚙️.dirname / "other.json"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "input"
        assert evaluate(root_module, "🐭.rebuild()") == "/data/sub/other.json"


def test_an_expression_may_reference_every_namespace():
    """Assignments read from 🐐, 🐭, 🐆 and ⚙️ alike."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_expression_namespaces.jaz
        🐐.global-value = "g"
        🐭.module-value = "m"

        go(local-value="l"):
            🐆.combined = "🐐.global-value🐭.module-value🐆.local-value"
            🐆.retval = 🐆.combined
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "gml"
