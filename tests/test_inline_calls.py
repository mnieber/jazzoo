"""Calling a function from inside a shell line or shebang block.

A reference substitutes inline, and so does a call: `echo "Hello 🐭.f(x="y")!"`
splices the call's return value into the line before the interpreter sees it. The
call is found by reading jazzoo's own argument syntax from the sigil to the matching
parenthesis, so the surrounding block stays opaque (design section 11).

A `(` must follow the name directly. A space before it means the parenthesis is
ordinary text, which is what keeps `echo "Hello 🐆.who (see notes)"` a shell line.
"""

import pytest

from jazzoo import evaluate, parse_module
from jazzoo.runtime.utils.test_utils import save_fixture

pytestmark = pytest.mark.stage(2)


def test_a_call_substitutes_inline_like_a_reference():
    """A call inside a shell line is replaced by its return value."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_inline_basic.jaz
        [private]
        _get-name(uppercase="false"):
            #!/usr/bin/env bash
            if [ "🐆.uppercase" = "true" ]; then echo "JANE"; else echo "jane"; fi

        shouty():
            echo "Hello 🐭._get-name(uppercase="true")!"

        quiet():
            echo "Hello 🐭._get-name()!"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # The argument's quotes are jazzoo's, not the shell's - sweeping happens
        # before the line is handed to bash.
        assert evaluate(root_module, "🐭.shouty()") == "Hello JANE!"
        assert evaluate(root_module, "🐭.quiet()") == "Hello jane!"


def test_a_closing_paren_inside_an_argument_does_not_end_the_call():
    """The call ends at its matching parenthesis, so a `)` inside a quoted argument
    value is part of the argument."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_inline_paren_in_arg.jaz
        [private]
        _echo-arg(value):
            #!/usr/bin/env bash
            echo "🐆.value"

        go():
            echo "[🐭._echo-arg(value="a)b")]"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # A naive scan to the first `)` would cut the argument at `a`.
        assert evaluate(root_module, "🐭.go()") == "[a)b]"


def test_a_call_may_be_nested_in_an_argument():
    """An argument may itself be a call, so the scanner tracks nesting."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_inline_nested.jaz
        [private]
        _inner():
            #!/usr/bin/env bash
            echo "in"

        [private]
        _outer(value):
            #!/usr/bin/env bash
            echo "[🐆.value]"

        go():
            echo "🐭._outer(value=🐭._inner())"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "[in]"


def test_a_space_before_the_paren_means_it_is_not_a_call():
    """A reference followed by a space and a bracket is a shell line, not a call -
    which is what keeps ordinary parentheticals working."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_inline_space_is_text.jaz
        🐭.tracing = "on"

        greet(who):
            echo "Hello 🐆.who (tracing=🐭.tracing)"
        """)

        # Run
        # Loading alone is part of the assertion: validation must not read
        # `who (...)` as a call to a function that does not exist.
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert (
            evaluate(root_module, '🐭.greet(who="jane")')
            == "Hello jane (tracing=on)"
        )


def test_a_call_substitutes_inside_a_shebang_block():
    """Inline calls work in an alternative interpreter too, since substitution
    happens before the block is executed."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_inline_in_shebang.jaz
        [private]
        _name():
            #!/usr/bin/env bash
            echo "jane"

        go():
            #!/usr/bin/env python3
            print("Hello 🐭._name(), from python")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "Hello jane, from python"
