import os

import pytest

from jazzoo.modules.errors import ArgumentError, ExecutionError, ResolutionError
from jazzoo.modules.rules.parse_module import parse_module
from jazzoo.modules.rules.get_function_by_path import get_function_by_path
from jazzoo.modules.rules.get_targets import get_targets
from jazzoo.modules.rules.eval import eval
from jazzoo.runtime.utils.test_utils import save_fixture


def test_function_without_parameters():
    """A function with no parameters is a target and has an empty parameter list."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_no_params.jaz
        okay():
            #!/usr/bin/env bash
            echo "okay"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        fn = get_function_by_path(root_module, "okay")

        # Assert
        assert fn.parameters == []
        assert fn.is_target is True
        assert fn in get_targets(root_module)


def test_parameters_and_defaults():
    """Parameters are always named. A parameter either has a default value, or is
    required - in which case its default is None."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_params.jaz
        build(target, mode="release"):
            #!/usr/bin/env bash
            echo "🐆.target 🐆.mode"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        fn = get_function_by_path(root_module, "build")

        # Assert
        assert [p.name for p in fn.parameters] == ["target", "mode"]
        assert fn.parameters[0].default is None
        assert fn.parameters[1].default == "release"


def test_arguments_are_resolved_into_local_variables():
    """At call time the arguments are validated against the parameters, and the
    resolved values are read from the 🐆 namespace by the body."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_args_resolved.jaz
        build(target, mode="release"):
            #!/usr/bin/env bash
            echo "🐆.target-🐆.mode"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert eval(root_module, '🐭.build(target="myapp")') == "myapp-release"
        assert (
            eval(root_module, '🐭.build(target="myapp", mode="debug")') == "myapp-debug"
        )


def test_private_functions_are_not_targets():
    """A [private] function is not a target: it is not listed by `jaz --list` and
    cannot be invoked from the CLI, but it remains callable from within .jaz files."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_private.jaz
        [private]
        _helper(name):
            #!/usr/bin/env bash
            echo "Internal helper: 🐆.name"

        debug(name="me"):
            #!/usr/bin/env bash
            echo "debug"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        helper = get_function_by_path(root_module, "_helper")
        debug = get_function_by_path(root_module, "debug")

        # Assert
        assert helper is not None
        assert helper.is_target is False
        assert helper not in get_targets(root_module)
        assert (
            eval(root_module, '🐭._helper(name="anonymous")')
            == "Internal helper: anonymous"
        )

        assert debug.is_target is True
        assert get_targets(root_module) == [debug]


def test_mid_body_call_to_module_function():
    """Functions in the current module can be called mid-body using the 🐭 sigil."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_mid_body_call.jaz
        [private]
        _helper(name):
            #!/usr/bin/env bash
            echo "Internal helper: 🐆.name"

        debug(name="me"):
            🐆.retval = 🐭._helper(name="anonymous")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert eval(root_module, "🐭.debug()") == "Internal helper: anonymous"


def test_mid_body_call_to_imported_module():
    """Calls to imported modules use the module alias."""
    if True:
        # Config
        save_fixture("""# docker.jaz
        build(target):
            #!/usr/bin/env bash
            echo "building 🐆.target"
        """)

        jazzoo_fn = save_fixture("""# test_call_imported.jaz
        from ./docker.jaz import build as docker

        deploy():
            🐆.retval = 🐭.docker.build(target="myapp")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert eval(root_module, "🐭.deploy()") == "building myapp"


def test_dependencies_run_before_the_body():
    """Dependencies are declared after the colon, before the body, and run first."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_dependencies.jaz
        [private]
        _helper(name):
            #!/usr/bin/env bash
            echo "Internal helper: 🐆.name"
            🐭.name = 🐆.name

        debug(name="me"): _helper(name=🐆.name)
            #!/usr/bin/env bash
            echo "Running debug for: 🐭.name"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        debug = get_function_by_path(root_module, "debug")

        # Assert
        assert [d.name for d in debug.dependencies] == ["_helper"]
        assert (
            eval(root_module, '🐭.debug(name="maarten")')
            == "Running debug for: maarten"
        )


def test_dependency_arguments_may_reference_globals_and_parameters():
    """Dependency arguments may reference 🐐, 🐭 and the function's own parameters."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_dependency_args.jaz
        🐐.log-level = "high"
        🐭.tracing = "on"

        [private]
        _report(level, tracing, name):
            #!/usr/bin/env bash
            🐭.msg = "🐆.level 🐆.tracing 🐆.name"

        debug(name="me"): _report(level=🐐.log-level, tracing=🐭.tracing, name=🐆.name)
            echo "🐭.msg!"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert eval(root_module, "🐭.debug()") == "high on me!"


def test_function_returns_the_output_of_its_last_step():
    """Every step sets 🐆.retval from its stdout, so a function returns the output
    of the last step that ran."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_last_step.jaz
        make-full-path(input):
            #!/usr/bin/env bash
            echo "/data/🐆.input"

        two-steps():
            #!/usr/bin/env bash
            echo "first"

            #!/usr/bin/env bash
            echo "second"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert (
            eval(root_module, '🐭.make-full-path(input="input.json")')
            == "/data/input.json"
        )
        # Only the last step's output survives - the first one was overwritten.
        assert eval(root_module, "🐭.two-steps()") == "second"


def test_stdout_is_the_value_for_every_interpreter():
    """A shebang block returns whatever it writes to stdout, in any interpreter."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_stdout_is_value.jaz
        from-bash():
            #!/usr/bin/env bash
            echo "/etc/jazzoo.conf"

        from-python():
            #!/usr/bin/env python3
            print("/etc/jazzoo.conf")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert eval(root_module, "🐭.from-bash()") == "/etc/jazzoo.conf"
        assert eval(root_module, "🐭.from-python()") == "/etc/jazzoo.conf"


def test_retval_strips_one_trailing_newline():
    """⚙️.stdout is the raw stdout; ⚙️.output is the same with a single trailing
    newline removed."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_retval_newline.jaz
        speak():
            #!/usr/bin/env bash
            echo "one"
            echo "two"

        check():
            #!/usr/bin/env bash
            echo "one"
            echo "two"

            #!
            🐆.retval = ⚙️.stdout
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # echo emits a trailing newline; only that one is removed.
        assert eval(root_module, "🐭.speak()") == "one\ntwo"
        assert eval(root_module, "🐭.check()") == "one\ntwo\n"


def test_explicit_retval_assignment_overrides_the_last_step():
    """A body can assign 🐆.retval explicitly to return something other than its
    last step's output."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_explicit_retval.jaz
        make-full-path(input):
            🐆.retval = "/data/🐆.input"

        keep-earlier-output():
            echo "the value I want"
            🐆.wanted = ⚙️.output
            echo "noise"
            🐆.retval = 🐆.wanted
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert (
            eval(root_module, '🐭.make-full-path(input="input.json")')
            == "/data/input.json"
        )
        assert eval(root_module, "🐭.keep-earlier-output()") == "the value I want"


def test_retvals_are_local_to_the_main_function():
    """A call that is not assigned silently discards any return value."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_discard_retval.jaz
        [private]
        _returns-something():
            🐆.retval = "discarded"

        debug():
            🐆.retval = "own value"
            🐭._returns-something()
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # The discarded return value does not become debug()'s return value.
        assert eval(root_module, "🐭.debug()") == "own value"


def test_local_variables_do_not_leak_to_the_caller():
    """🐆 variables are scoped to the function invocation and do not leak to the caller."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_locals_dont_leak.jaz
        [private]
        _sets-a-local():
            🐆.secret = "hidden"
            🐆.retval = "ok"

        debug():
            🐆.secret = "mine"
            🐭._sets-a-local()
            🐆.retval = 🐆.secret
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert eval(root_module, "🐭.debug()") == "mine"


def test_a_local_function_does_not_overwrite_the_callers_retval():
    """A local function has a fresh 🐆 namespace, including 🐆.retval and ⚙️.stdout:
    its own steps do not overwrite the enclosing function's."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_local_fn_retval.jaz
        help(who="me"):
            🐆.dump(who):
                #!/usr/bin/env bash
                echo "Hello 🐆.who!"

            #!/usr/bin/env bash
            echo "outer output"

            #!
            🐆.mine = 🐆.retval
            🐆.inner = 🐆.dump(who=🐆.who)
            🐆.retval = "🐆.inner / 🐆.mine"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert (
            eval(root_module, '🐭.help(who="maarten")')
            == "Hello maarten! / outer output"
        )
