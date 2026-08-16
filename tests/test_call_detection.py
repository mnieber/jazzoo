"""A jazzoo call is only a call when it is the whole line, or the whole right-hand
side of an assignment.

Found by running a real .jaz file rather than by the spec-tests: a shell line like
`echo "Hello 🐆.who (tracing=🐭.tracing)"` is call-shaped if you scan for a sigil
followed by a bracket, and was being validated as a call to a function named `who`.
"""

import pytest

from jazzoo import evaluate, parse_module
from jazzoo.runtime.utils.test_utils import save_fixture

pytestmark = pytest.mark.stage(1)


def test_a_reference_followed_by_a_bracket_is_not_a_call():
    """A shell line that merely contains a reference before a parenthesis is a shell
    line, not a jazzoo call."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bracket_not_a_call.jaz
        🐭.tracing = "on"

        greet(who):
            echo "Hello 🐆.who (tracing=🐭.tracing)"
        """)

        # Run
        # Loading alone is the regression: validation used to read `who (...)` as a
        # call to a function that does not exist.
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert (
            evaluate(root_module, '🐭.greet(who="jane")')
            == "Hello jane (tracing=on)"
        )


def test_a_call_as_an_assignment_right_hand_side_is_still_validated():
    """Anchoring the call pattern must not stop the right-hand side of an
    assignment from being checked at parse time."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_rhs_call_validated.jaz
        build(target):
            echo "🐆.target"

        go():
            🐆.retval = 🐭.build(nonesuch="x")
        """)

        # Run / Assert
        from jazzoo import ArgumentError

        with pytest.raises(ArgumentError):
            parse_module(jazzoo_fn)
