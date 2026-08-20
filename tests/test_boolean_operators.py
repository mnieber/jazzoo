"""The `and`, `or` and `not` operators (design section 5).

They combine values by truthiness, yield an operand rather than a plain boolean
(except `not`), short-circuit, and follow Python's precedence.
"""

import pytest

from jazzoo import (
    ArgumentError,
    ParseError,
    ResolutionError,
    evaluate,
    parse_module,
)
from jazzoo.runtime.utils.test_utils import save_fixture


def test_and_or_and_not_combine_truthiness():
    """`and`, `or` and `not` combine values by their truthiness."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bool_basic.jaz
        🐭.yes = true
        🐭.no = false

        both-true():
            🐆.retval = "y" if 🐭.yes and 🐭.yes else "n"

        one-false():
            🐆.retval = "y" if 🐭.yes and 🐭.no else "n"

        either():
            🐆.retval = "y" if 🐭.no or 🐭.yes else "n"

        neither():
            🐆.retval = "y" if 🐭.no or 🐭.no else "n"

        negated():
            🐆.retval = "y" if not 🐭.no else "n"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.both-true()") == "y"
        assert evaluate(root_module, "🐭.one-false()") == "n"
        assert evaluate(root_module, "🐭.either()") == "y"
        assert evaluate(root_module, "🐭.neither()") == "n"
        assert evaluate(root_module, "🐭.negated()") == "y"


def test_truthiness_follows_the_existing_rule():
    """The operators use the same truthiness as a ternary condition, so env-var
    style negatives are falsy."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bool_truthiness.jaz
        🐭.off = "no"
        🐭.zero = "0"
        🐭.empty = []
        🐭.on = "yes"

        go():
            🐆.retval = "y" if 🐭.off or 🐭.zero or 🐭.empty else "n"

        with-truthy():
            🐆.retval = "y" if 🐭.off or 🐭.on else "n"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "n"
        assert evaluate(root_module, "🐭.with-truthy()") == "y"


def test_and_and_or_yield_an_operand():
    """`and` and `or` yield one of their operands, not a plain boolean: `and` yields
    its left operand when that is falsy and otherwise its right, and `or` does the
    reverse."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bool_operand.jaz
        🐭.given = ""
        🐭.name = "jane"

        fallback():
            🐆.retval = 🐭.given or "anonymous"

        keeps-truthy():
            🐆.retval = 🐭.name or "anonymous"

        and-yields-right():
            🐆.retval = 🐭.name and "reached"

        and-yields-left():
            🐆.retval = 🐭.given and "not reached"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.fallback()") == "anonymous"
        assert evaluate(root_module, "🐭.keeps-truthy()") == "jane"
        assert evaluate(root_module, "🐭.and-yields-right()") == "reached"
        # The falsy left operand is handed back as-is.
        assert evaluate(root_module, "🐭.and-yields-left()") == ""


def test_not_always_yields_a_boolean():
    """`not` always yields a real boolean, since there is no operand to pass
    through."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bool_not.jaz
        🐭.verbose = "yes"
        🐭.quiet = ""

        negate-truthy():
            🐆.retval = not 🐭.verbose

        negate-falsy():
            🐆.retval = not 🐭.quiet
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # A boolean renders as `true` / `false`, not as the operand.
        assert evaluate(root_module, "🐭.negate-truthy()") == "false"
        assert evaluate(root_module, "🐭.negate-falsy()") == "true"


def test_precedence_follows_python():
    """Precedence, loosest first: `or`, then `and`, then `not`, then `==`. So
    `a or b and not c` reads as `a or (b and (not c))`."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bool_precedence.jaz
        🐭.t = true
        🐭.f = false

        or-binds-loosest():
            🐆.retval = "y" if 🐭.t or 🐭.f and 🐭.f else "n"

        not-binds-tighter-than-and():
            🐆.retval = "y" if 🐭.t and not 🐭.f else "n"

        equality-binds-tightest():
            🐆.retval = "y" if 🐭.t == true and 🐭.f == false else "n"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # `t or (f and f)` is true; `(t or f) and f` would be false.
        assert evaluate(root_module, "🐭.or-binds-loosest()") == "y"
        assert evaluate(root_module, "🐭.not-binds-tighter-than-and()") == "y"
        assert evaluate(root_module, "🐭.equality-binds-tightest()") == "y"


def test_parentheses_override_precedence():
    """Parentheses group, overriding the default precedence."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bool_parens.jaz
        🐭.t = true
        🐭.f = false

        grouped():
            🐆.retval = "y" if (🐭.t or 🐭.f) and 🐭.f else "n"

        ungrouped():
            🐆.retval = "y" if 🐭.t or 🐭.f and 🐭.f else "n"

        nested():
            🐆.retval = "y" if 🐭.t and not (🐭.f or 🐭.f) else "n"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # The parentheses flip the result relative to the ungrouped form.
        assert evaluate(root_module, "🐭.grouped()") == "n"
        assert evaluate(root_module, "🐭.ungrouped()") == "y"
        assert evaluate(root_module, "🐭.nested()") == "y"


def test_operators_short_circuit():
    """`or` does not evaluate its right operand when the left is truthy, and `and`
    does not when the left is falsy."""
    if True:
        # Config
        # The right operand writes a file, so whether it ran is observable.
        jazzoo_fn = save_fixture("""# test_bool_short_circuit.jaz
        🐭.truthy = "yes"
        🐭.falsy = ""

        [private]
        _marker():
            @echo "ran"

        or-skips-right():
            🐆.retval = 🐭.truthy or 🐭._marker()

        and-skips-right():
            🐆.retval = 🐭.falsy and 🐭._marker()

        or-needs-right():
            🐆.retval = 🐭.falsy or 🐭._marker()
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # The skipped call never ran, so its output is not the result.
        assert evaluate(root_module, "🐭.or-skips-right()") == "yes"
        assert evaluate(root_module, "🐭.and-skips-right()") == ""
        # When the left is falsy, `or` does evaluate the right.
        assert evaluate(root_module, "🐭.or-needs-right()") == "ran"


def test_short_circuiting_applies_to_resolution():
    """Short-circuiting applies to resolution as well, so an unresolvable reference
    on the skipped side raises nothing."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bool_short_circuit_resolution.jaz
        🐭.truthy = "yes"
        🐭.falsy = ""

        skipped():
            🐆.retval = 🐭.truthy or 🐭.never-defined

        evaluated():
            🐆.retval = 🐭.falsy or 🐭.never-defined
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.skipped()") == "yes"
        # The same reference does raise when it is actually reached.
        with pytest.raises(ResolutionError):
            evaluate(root_module, "🐭.evaluated()")


def test_boolean_operators_compose_with_the_rest_of_the_grammar():
    """The operators sit between the ternary and the existing operators, so a
    condition may mix them with equality and calls."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bool_compose.jaz
        🐭.level = "high"
        🐭.tracing = false

        go():
            🐆.retval = "loud" if 🐭.level == "high" and not 🐭.tracing else "quiet"

        with-call():
            🐆.retval = "y" if 🐭.name() or 🐭.tracing else "n"

        [private]
        name():
            @echo "jane"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "loud"
        assert evaluate(root_module, "🐭.with-call()") == "y"


def test_a_computed_function_value_can_be_called():
    """`and` and `or` yield an operand, so when the operands are functions the
    result is a function - and it can be called directly."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bool_call_result.jaz
        🐭.absent = ""

        [private]
        f1(x="?"):
            @echo "f1 got 🐆.x"

        [private]
        f2(x="?"):
            @echo "f2 got 🐆.x"

        picks-left():
            🐆.retval = (🐭.f1 or 🐭.f2)(x="3")

        picks-right():
            🐆.retval = (🐭.absent or 🐭.f2)(x="3")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.picks-left()") == "f1 got 3"
        assert evaluate(root_module, "🐭.picks-right()") == "f2 got 3"

    """The same value may be stored first and called afterwards."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bool_call_stored.jaz
        [private]
        f1(x="?"):
            @echo "f1 got 🐆.x"

        [private]
        f2(x="?"):
            @echo "f2 got 🐆.x"

        go():
            🐆.chosen = 🐭.f1 or 🐭.f2
            🐆.retval = 🐆.chosen(x="3")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "f1 got 3"

    """A curried operand keeps its bindings when the result is called."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bool_call_curried.jaz
        🐭.absent = ""

        [private]
        f1(x, y="?"):
            @echo "f1 🐆.x/🐆.y"

        go():
            🐆.retval = (🐭.absent or 🐭.f1[y="bound"])(x="3")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "f1 3/bound"


def test_a_computed_function_value_can_be_piped_into():
    """A pipe stage may be a computed expression: it is evaluated, and the piped
    value is applied to whatever function it produced."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bool_pipe_into.jaz
        🐭.absent = ""

        [private]
        f1(x="?"):
            @echo "f1 got 🐆.x"

        [private]
        f2(x="?"):
            @echo "f2 got 🐆.x"

        picks-left():
            🐆.retval = "3" | (🐭.f1 or 🐭.f2)

        picks-right():
            🐆.retval = "3" | (🐭.absent or 🐭.f2)
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.picks-left()") == "f1 got 3"
        assert evaluate(root_module, "🐭.picks-right()") == "f2 got 3"


def test_a_module_level_variable_may_hold_a_chosen_function():
    """A module-level assignment from `and`/`or` holds the chosen function, exactly
    as a plain alias does, and can be called through."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bool_module_level.jaz
        [private]
        f1(x="?"):
            @echo "f1 got 🐆.x"

        [private]
        f2(x="?"):
            @echo "f2 got 🐆.x"

        🐭.chosen = 🐭.f1 or 🐭.f2

        go():
            🐆.retval = 🐭.chosen(x="3")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "f1 got 3"


def test_calling_a_value_that_may_not_be_a_function_is_an_error():
    """A name is only safely callable when every branch yields a function. One that
    may yield a non-function cannot always be called, so calling it is an error."""
    if True:
        # Config
        # The left operand is not a function at all; the right one is.
        jazzoo_fn = save_fixture("""# test_bool_alternatives.jaz
        🐭.absent = ""

        [private]
        g1(y="?"):
            @echo "g1:🐆.y"

        go():
            🐆.chosen = 🐭.absent or 🐭.g1
            🐆.retval = 🐆.chosen(y="1")
        """)

        # Run / Assert
        with pytest.raises(ParseError) as error:
            parse_module(jazzoo_fn)
        assert "is not a function" in error.value.message


def test_a_mixed_value_that_is_never_called_is_fine():
    """The check belongs to the call site: assigning such a value is fine, and only
    calling through it is an error."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bool_mixed_uncalled.jaz
        🐭.absent = ""

        [private]
        g1(y="?"):
            @echo "g1:🐆.y"

        go():
            🐆.thing = 🐭.absent or 🐭.g1
            @echo "assigned, never called"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "assigned, never called"


def test_a_pure_value_fallback_is_unaffected():
    """`or` over plain values stays the documented fallback idiom - no function is
    involved, so nothing is called and nothing is checked."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bool_value_fallback.jaz
        🐭.given = ""

        go():
            🐆.name = 🐭.given or "anonymous"
            🐆.retval = 🐆.name
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "anonymous"


def test_every_candidate_must_accept_the_call():
    """Which candidate runs is decided at run time, so every one of them must accept
    the call - that is what makes it correct whichever operand wins."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bool_alternatives_bad.jaz
        [private]
        f1(x="?"):
            @echo "f1:🐆.x"

        [private]
        g1(y="?"):
            @echo "g1:🐆.y"

        go():
            🐆.chosen = 🐭.f1 or 🐭.g1
            🐆.retval = 🐆.chosen(zzz="1")
        """)

        # Run / Assert
        with pytest.raises(ArgumentError):
            parse_module(jazzoo_fn)


def test_a_call_only_one_candidate_accepts_is_rejected():
    """A call correct for one operand but not the other is rejected at load time,
    since the wrong one may be the one that runs."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bool_alternatives_partial.jaz
        [private]
        f1(x="?"):
            @echo "f1:🐆.x"

        [private]
        g1(y="?"):
            @echo "g1:🐆.y"

        go():
            🐆.chosen = 🐭.f1 or 🐭.g1
            🐆.retval = 🐆.chosen(y="1")
        """)

        # Run / Assert
        # `g1` would accept `y`, but `f1` would not - and either may win.
        with pytest.raises(ArgumentError) as error:
            parse_module(jazzoo_fn)
        assert "no parameter named 'y'" in error.value.message


def test_parentheses_may_hold_a_ternary():
    """A group re-enters at the top of the grammar, so it may contain a ternary."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bool_paren_ternary.jaz
        🐭.c = true
        🐭.z = "fallback"

        go():
            🐆.retval = ("x" if 🐭.c else "y") or 🐭.z
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "x"


def test_the_documented_example():
    """The example from the design doc."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bool_documented.jaz
        🐭.test = false

        go(foo, bar):
            🐆.doit = "yes" if 🐆.foo or (🐆.bar and not 🐭.test) else "no"
            🐆.retval = 🐆.doit
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, '🐭.go(foo="1", bar="")') == "yes"
        assert evaluate(root_module, '🐭.go(foo="", bar="1")') == "yes"
        assert evaluate(root_module, '🐭.go(foo="", bar="")') == "no"
