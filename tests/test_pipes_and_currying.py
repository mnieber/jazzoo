import pytest

from jazzoo.modules.errors import ArgumentError, ResolutionError
from jazzoo.modules.rules.parse_module import parse_module
from jazzoo.modules.rules.evaluate import evaluate
from jazzoo.runtime.utils.test_utils import save_fixture

# A library module of small string helpers, used as pipe stages.
save_fixture("""# helpers.jaz
make-full-path(input, style="posix"):
    #!/usr/bin/env bash
    echo "/data/🐆.style/🐆.input"

drop-config-dir-part(path):
    #!/usr/bin/env bash
    echo "🐆.path" | sed 's|/config||'

clean_up(name, max_length="10", suffix=""):
    #!/usr/bin/env bash
    echo "🐆.name🐆.suffix" | cut -c1-🐆.max_length
""")


def test_currying_binds_a_parameter():
    """Square brackets create a curried function in which the named parameter is
    bound, so the caller may no longer supply an argument for it."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_curry_binds.jaz
        from ./helpers.jaz import make-full-path as h

        🐭.build-windows = 🐭.h.make-full-path[style="windows"]

        go():
            🐆.retval = 🐭.build-windows(input="input.json")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "/data/windows/input.json"


def test_currying_leaves_other_parameters_open():
    """Parameters that are not bound by the curry expression are still supplied by
    the caller."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_curry_open.jaz
        from ./helpers.jaz import make-full-path as h

        🐭.build = 🐭.h.make-full-path[style="linux"]

        go():
            🐆.retval = 🐭.build(input="a.json")

        go2():
            🐆.retval = 🐭.build(input="b.json")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "/data/linux/a.json"
        assert evaluate(root_module, "🐭.go2()") == "/data/linux/b.json"


def test_empty_brackets_are_the_function_itself():
    """`f[]` binds no parameters and is equivalent to the bare function symbol.
    `f()` is different - it calls the function."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_empty_brackets.jaz
        from ./helpers.jaz import make-full-path as h

        🐭.a = 🐭.h.make-full-path[]
        🐭.b = 🐭.h.make-full-path

        go():
            🐆.retval = 🐭.a(input="x.json")

        go2():
            🐆.retval = 🐭.b(input="x.json")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "/data/posix/x.json"
        assert evaluate(root_module, "🐭.go2()") == "/data/posix/x.json"


def test_bare_name_marks_a_parameter_as_unbound():
    """A bare parameter name inside the brackets marks it as explicitly unbound;
    every other parameter is bound in the curry expression or by its default."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bare_name.jaz
        from ./helpers.jaz import clean_up as h

        🐭.shorten = 🐭.h.clean_up[name, max_length="3"]

        go():
            🐆.retval = 🐭.shorten(name="jane")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # max_length is bound to 3, suffix falls back to its default, name is open.
        assert evaluate(root_module, "🐭.go()") == "maa"


def test_pipe_feeds_the_unbound_parameter():
    """The piped value becomes the argument for the stage's single unbound
    parameter."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_pipe_single.jaz
        from ./helpers.jaz import make-full-path as h

        go():
            🐆.retval = "input.json" | 🐭.h.make-full-path[style="linux"]
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "/data/linux/input.json"


def test_pipe_without_brackets():
    """A stage piped without brackets is the same as `f[]`, so it must declare
    exactly one parameter in total - otherwise the free one is ambiguous."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_pipe_no_brackets.jaz
        from ./helpers.jaz import drop-config-dir-part as h

        go():
            🐆.retval = "/data/config/input.json" | 🐭.h.drop-config-dir-part
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "/data/input.json"


def test_the_free_parameter_must_be_unambiguous():
    """A function with more than one parameter must say which parameter is free,
    even when the others all have defaults. Naming it bare and binding everything
    else are equivalent."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_free_param.jaz
        from ./helpers.jaz import make-full-path as h

        by-naming-the-free-one():
            🐆.retval = "input.json" | 🐭.h.make-full-path[input]

        by-binding-the-rest():
            🐆.retval = "input.json" | 🐭.h.make-full-path[style="posix"]
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # `input` is free and takes the piped value; `style` falls back to its default.
        assert (
            evaluate(root_module, "🐭.by-naming-the-free-one()")
            == "/data/posix/input.json"
        )
        assert (
            evaluate(root_module, "🐭.by-binding-the-rest()")
            == "/data/posix/input.json"
        )


def test_pipe_chain_passes_return_values_onwards():
    """Each stage's return value is piped onwards to the next stage."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_pipe_chain.jaz
        from ./helpers.jaz import * as h

        go():
            🐆.retval = "input.json" \\
                | 🐭.h.make-full-path[style="config"] \\
                | 🐭.h.drop-config-dir-part \\
                | 🐭.h.clean_up[name, max_length="7"]
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # "input.json" -> "/data/config/input.json" -> "/data/input.json" -> "/data/i"
        assert evaluate(root_module, "🐭.go()") == "/data/i"


def test_pipe_applies_to_builtin_functions():
    """Built-in ⚙️ functions are piped exactly like user functions."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_pipe_builtin.jaz
        go():
            🐆.retval = "/data/sub/../input.json" | ⚙️.abs

        go2():
            🐆.retval = "/data/input.json" | ⚙️.basename | ⚙️.stem
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "/data/input.json"
        assert evaluate(root_module, "🐭.go2()") == "input"


def test_a_pipe_stage_binding_every_parameter_is_an_argument_error():
    """A pipe stage must leave exactly one parameter unbound. Binding them all
    leaves nowhere for the piped value to go, and is an ArgumentError."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_pipe_zero_unbound.jaz
        from ./helpers.jaz import make-full-path as h

        go():
            🐆.retval = "x.json" | 🐭.h.make-full-path[input="a.json", style="linux"]
        """)

        # Run / Assert
        with pytest.raises(ArgumentError):
            parse_module(jazzoo_fn)


def test_a_pipe_stage_leaving_two_parameters_unbound_is_an_argument_error():
    """A pipe stage that leaves more than one parameter unbound is ambiguous - which
    parameter is free must be decidable from the expression alone, and defaults play
    no part in deciding it."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_pipe_two_unbound.jaz
        from ./helpers.jaz import make-full-path as h

        go():
            🐆.retval = "x.json" | 🐭.h.make-full-path
        """)

        # Run / Assert
        # make-full-path(input, style="posix") has two parameters, so the bare
        # symbol - equivalent to `[]` - leaves both unbound, even though `style`
        # has a default.
        with pytest.raises(ArgumentError):
            parse_module(jazzoo_fn)


def test_binding_an_unknown_parameter_in_a_curry_is_an_argument_error():
    """A curry expression may only bind parameters the function declares."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_curry_unknown_param.jaz
        from ./helpers.jaz import make-full-path as h

        🐭.build = 🐭.h.make-full-path[nonesuch="x"]
        """)

        # Run / Assert
        with pytest.raises(ArgumentError):
            parse_module(jazzoo_fn)


def test_naming_an_unknown_parameter_as_unbound_is_an_argument_error():
    """A bare name in the brackets marks a parameter unbound, so it too must name a
    parameter the function declares."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_curry_unknown_bare_name.jaz
        from ./helpers.jaz import make-full-path as h

        🐭.build = 🐭.h.make-full-path[nonesuch, style="linux"]
        """)

        # Run / Assert
        with pytest.raises(ArgumentError):
            parse_module(jazzoo_fn)


def test_supplying_an_argument_for_a_bound_parameter_is_an_argument_error():
    """Currying binds a parameter, and the caller may no longer supply an argument
    for it."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_curry_rebind.jaz
        from ./helpers.jaz import make-full-path as h

        🐭.build-windows = 🐭.h.make-full-path[style="windows"]

        go():
            🐆.retval = 🐭.build-windows(input="input.json", style="linux")
        """)

        # Run / Assert
        with pytest.raises(ArgumentError):
            parse_module(jazzoo_fn)


def test_a_variable_holding_a_function_is_callable():
    """Assigning a function symbol to a variable makes that variable callable - the
    function symbol is equivalent to applying empty square brackets to it."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_variable_is_callable.jaz
        [private]
        _greet(who, punctuation="!"):
            echo "Hello 🐆.who🐆.punctuation"

        🐭.greet = 🐭._greet

        go():
            🐆.retval = 🐭.greet(who="jane")

        with-every-argument():
            🐆.retval = 🐭.greet(who="jane", punctuation="?")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # The variable behaves as the function it holds, defaults included.
        assert evaluate(root_module, "🐭.go()") == "Hello jane!"
        assert evaluate(root_module, "🐭.with-every-argument()") == "Hello jane?"


def test_a_local_variable_may_hold_and_call_a_function():
    """A 🐆 variable can hold a function too, and is called the same way."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_local_variable_is_callable.jaz
        [private]
        _greet(who):
            echo "Hello 🐆.who"

        go():
            🐆.greet = 🐭._greet
            🐆.retval = 🐆.greet(who="jane")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "Hello jane"


def test_a_variable_holding_a_function_can_be_reassigned_and_piped():
    """A variable holding a function is an ordinary value: it can be passed onwards
    to another variable, and used as a pipe stage."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_function_value_flows.jaz
        from ./helpers.jaz import drop-config-dir-part as h

        🐭.first = 🐭.h.drop-config-dir-part
        🐭.second = 🐭.first

        called():
            🐆.retval = 🐭.second(path="/data/config/input.json")

        piped():
            🐆.retval = "/data/config/input.json" | 🐭.second
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.called()") == "/data/input.json"
        assert evaluate(root_module, "🐭.piped()") == "/data/input.json"


def test_calling_a_variable_that_holds_a_string_is_an_error():
    """Only a variable holding a function is callable. Calling one that holds an
    ordinary string does not resolve to a function."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_calling_a_string.jaz
        🐭.not-a-function = "just a string"

        go():
            🐆.retval = 🐭.not-a-function()
        """)

        # Run / Assert
        with pytest.raises(ResolutionError):
            parse_module(jazzoo_fn)


def test_calling_a_function_symbol_without_arguments_is_an_error():
    """`🐭.foo = 🐭.build()` is an error, because it executes `build` without passing
    any arguments rather than referring to it."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_symbol_vs_call.jaz
        from ./helpers.jaz import make-full-path as h

        🐭.executed-too-early = 🐭.h.make-full-path()
        """)

        # Run / Assert
        # `make-full-path` requires `input`, so calling it here is a missing argument.
        with pytest.raises(ArgumentError):
            parse_module(jazzoo_fn)
