"""Local functions - functions scoped to 🐆, defined inside another function.

The interaction between a local function's 🐆.retval and its caller's is covered by
test_a_local_function_does_not_overwrite_the_callers_retval in test_functions.py.
"""

import pytest

from jazzoo import (
    ArgumentError,
    ResolutionError,
    evaluate,
    get_function_by_path,
    get_targets,
    parse_module,
)
from jazzoo.runtime.utils.test_utils import save_fixture


@pytest.mark.stage(6)
def test_a_local_function_is_called_with_named_arguments():
    """Local functions declare parameters and are called with named arguments exactly
    like 🐭 functions."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_local_basic.jaz
        🐭.tracing = "on"

        help(who="me"):
            🐆.dump(who):
                echo "Hello 🐆.who! Tracing is: 🐭.tracing"

            🐆.retval = 🐆.dump(who=🐆.who)
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.help()") == "Hello me! Tracing is: on"
        assert (
            evaluate(root_module, '🐭.help(who="jane")') == "Hello jane! Tracing is: on"
        )


@pytest.mark.stage(6)
def test_a_local_function_takes_parameter_defaults():
    """A local function's parameters may have defaults, like any other function."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_local_defaults.jaz
        help():
            🐆.greet(who="world", punctuation="!"):
                echo "Hello 🐆.who🐆.punctuation"

            🐆.retval = 🐆.greet()
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.help()") == "Hello world!"


@pytest.mark.stage(6)
def test_a_positional_argument_to_a_local_function_is_an_argument_error():
    """Arguments are always named, in local functions too."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_local_positional.jaz
        help():
            🐆.dump(who):
                echo "Hello 🐆.who"

            🐆.retval = 🐆.dump("me")
        """)

        # Run / Assert
        with pytest.raises(ArgumentError):
            parse_module(jazzoo_fn)


@pytest.mark.stage(6)
def test_a_missing_argument_to_a_local_function_is_an_argument_error():
    """A local function's required parameters are validated like any other."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_local_missing_arg.jaz
        help():
            🐆.dump(who):
                echo "Hello 🐆.who"

            🐆.retval = 🐆.dump()
        """)

        # Run / Assert
        with pytest.raises(ArgumentError):
            parse_module(jazzoo_fn)


@pytest.mark.stage(6)
def test_a_local_function_has_a_fresh_local_namespace():
    """Local functions have their own fresh 🐆 namespace - variables set inside do not
    leak to the parent."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_local_namespace_fresh.jaz
        help():
            🐆.secret = "parent"

            🐆.dump():
                🐆.secret = "child"
                🐆.retval = "🐆.secret"

            🐆.from-child = 🐆.dump()
            🐆.retval = "🐆.from-child/🐆.secret"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # The child set its own 🐆.secret; the parent's is untouched.
        assert evaluate(root_module, "🐭.help()") == "child/parent"


@pytest.mark.stage(6)
def test_arguments_are_passed_explicitly_not_inherited():
    """A local function does not see the enclosing function's 🐆 variables - arguments
    are passed explicitly."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_local_no_inheritance.jaz
        help(who="me"):
            🐆.dump():
                echo "[🐆.who?]"

            🐆.retval = 🐆.dump()
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # The `?` marker keeps this a resolution to the empty string rather than an
        # error - what matters is that `who` did not carry into the local function.
        assert evaluate(root_module, "🐭.help()") == "[]"

    """Without the `?` marker, the same reference is a ResolutionError."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_local_no_inheritance_strict.jaz
        help(who="me"):
            🐆.dump():
                echo "[🐆.who]"

            🐆.retval = 🐆.dump()
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        with pytest.raises(ResolutionError):
            evaluate(root_module, "🐭.help()")


@pytest.mark.stage(6)
def test_a_local_function_sees_module_and_global_variables():
    """Only 🐆 is fresh: 🐭 resolves against the defining file and 🐐 is global, so
    both are visible inside a local function."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_local_sees_outer_scopes.jaz
        🐐.log-level = "high"
        🐭.tracing = "on"

        help():
            🐆.dump():
                echo "🐐.log-level/🐭.tracing"

            🐆.retval = 🐆.dump()
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.help()") == "high/on"


@pytest.mark.stage(6)
def test_a_local_function_is_not_visible_outside_its_enclosing_function():
    """Local functions are only accessible within the enclosing function - they are
    not 🐭 functions and not targets."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_local_not_visible.jaz
        help():
            🐆.dump():
                echo "hello"

            🐆.retval = 🐆.dump()

        other():
            echo "other"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # It is not reachable in the module namespace ...
        assert get_function_by_path(root_module, "dump") is None
        # ... and it is not a target.
        assert {f.name for f in get_targets(root_module)} == {"help", "other"}


@pytest.mark.stage(6)
def test_calling_a_local_function_from_another_function_is_a_resolution_error():
    """A local function defined in one function cannot be called from another."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_local_out_of_scope.jaz
        help():
            🐆.dump():
                echo "hello"

            🐆.retval = 🐆.dump()

        other():
            🐆.retval = 🐆.dump()
        """)

        # Run / Assert
        with pytest.raises(ResolutionError):
            parse_module(jazzoo_fn)


@pytest.mark.stage(6)
def test_local_functions_support_shebang_blocks():
    """Local functions support the same body forms as regular functions: shell lines,
    assignments, and shebang blocks."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_local_body_forms.jaz
        help():
            🐆.dump(who):
                #!/usr/bin/env python3
                print("Hello 🐆.who, from python")

            🐆.retval = 🐆.dump(who="jane")

        with-an-assignment():
            🐆.dump(who):
                🐆.greeting = "Hello"
                echo "🐆.greeting 🐆.who"

            🐆.retval = 🐆.dump(who="jane")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.help()") == "Hello jane, from python"
        assert evaluate(root_module, "🐭.with-an-assignment()") == "Hello jane"


@pytest.mark.stage(6)
def test_local_functions_nest():
    """Local functions support nested local functions."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_local_nested.jaz
        help():
            🐆.outer(who):
                🐆.inner(name):
                    echo "inner: 🐆.name"

                🐆.retval = 🐆.inner(name=🐆.who)

            🐆.retval = 🐆.outer(who="jane")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.help()") == "inner: jane"


@pytest.mark.stage(6)
def test_a_nested_local_function_is_scoped_to_its_own_parent():
    """A nested local function is scoped to the function that defines it, so the
    outermost function cannot call it."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_local_nested_scope.jaz
        help():
            🐆.outer():
                🐆.inner():
                    echo "inner"

                🐆.retval = 🐆.inner()

            🐆.retval = 🐆.inner()
        """)

        # Run / Assert
        with pytest.raises(ResolutionError):
            parse_module(jazzoo_fn)


@pytest.mark.stage(6)
def test_a_local_function_may_call_module_functions():
    """A local function can call 🐭 functions, which resolve against the defining
    file as they do anywhere else."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_local_calls_module_fn.jaz
        [private]
        _helper(name):
            echo "helper: 🐆.name"

        help():
            🐆.dump(who):
                🐆.retval = 🐭._helper(name=🐆.who)

            🐆.retval = 🐆.dump(who="jane")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.help()") == "helper: jane"


@pytest.mark.stage(1)
def test_the_at_marker_suppresses_console_output(capsys):
    """jazzoo prints each command to the console so the caller can see what is being
    executed. Prefixing the line with `@` suppresses that."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_at_marker.jaz
        loud():
            echo "Hello"

        quiet():
            @echo "Hello"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        loud_retval = evaluate(root_module, "🐭.loud()")
        loud_console = capsys.readouterr()

        quiet_retval = evaluate(root_module, "🐭.quiet()")
        quiet_console = capsys.readouterr()

        # Assert
        # `@` hides the echoed command, not the command's own output, so both
        # functions still return the same value.
        assert loud_retval == "Hello"
        assert quiet_retval == "Hello"
        assert 'echo "Hello"' in loud_console.out
        assert 'echo "Hello"' not in quiet_console.out


@pytest.mark.stage(6)
def test_the_at_marker_applies_inside_a_local_function(capsys):
    """The `@` marker works on the lines of a local function body too."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_at_marker_local.jaz
        help(who="me"):
            🐆.dump(who):
                @echo "Hello 🐆.who!"

            🐆.retval = 🐆.dump(who=🐆.who)
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        retval = evaluate(root_module, '🐭.help(who="jane")')
        console = capsys.readouterr()

        # Assert
        assert retval == "Hello jane!"
        assert "echo" not in console.out
