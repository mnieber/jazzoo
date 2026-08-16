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
        assert eval(root_module, '🐭.debug(name="jane")') == "Running debug for: jane"


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
        assert eval(root_module, '🐭.help(who="jane")') == "Hello jane! / outer output"


def test_a_positional_argument_is_an_argument_error():
    """Within .jaz files all arguments must be named, so a positional argument at a
    call site is an ArgumentError - raised at parse time, before anything runs."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_positional_arg.jaz
        build(target, mode="release"):
            #!/usr/bin/env bash
            echo "🐆.target 🐆.mode"

        test():
            🐭.build("dev")
        """)

        # Run / Assert
        with pytest.raises(ArgumentError):
            parse_module(jazzoo_fn)


def test_a_missing_required_argument_is_an_argument_error():
    """A parameter without a default is required; a call that does not supply an
    argument for it is an ArgumentError at parse time."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_missing_required_arg.jaz
        build(target, mode="release"):
            #!/usr/bin/env bash
            echo "🐆.target 🐆.mode"

        test():
            🐭.build()
        """)

        # Run / Assert
        # `mode` has a default and may be omitted; `target` may not.
        with pytest.raises(ArgumentError):
            parse_module(jazzoo_fn)


def test_an_unknown_argument_name_is_an_argument_error():
    """A call supplying an argument the function has no parameter for is an
    ArgumentError."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_unknown_arg.jaz
        build(target, mode="release"):
            #!/usr/bin/env bash
            echo "🐆.target 🐆.mode"

        test():
            🐭.build(target="myapp", profile="dev")
        """)

        # Run / Assert
        with pytest.raises(ArgumentError):
            parse_module(jazzoo_fn)


def test_a_call_to_an_unknown_function_is_a_resolution_error():
    """A call to a function that does not exist is a ResolutionError at parse time."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_unknown_function.jaz
        test():
            🐭.no-such-function()
        """)

        # Run / Assert
        with pytest.raises(ResolutionError):
            parse_module(jazzoo_fn)


def test_a_call_to_an_unknown_module_is_a_resolution_error():
    """A call through a namespace alias that was never imported is a
    ResolutionError - unknown modules and namespaces resolve like unknown
    functions do."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_unknown_module.jaz
        test():
            🐭.nope.bar()
        """)

        # Run / Assert
        with pytest.raises(ResolutionError):
            parse_module(jazzoo_fn)


def test_a_shebang_block_exiting_non_zero_is_an_execution_error():
    """A shebang block that exits non-zero is an ExecutionError. This is a run-time
    error: the file parses, and the failure surfaces only when the target runs."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_non_zero_exit.jaz
        explicit-exit():
            #!/usr/bin/env bash
            exit 3

        failing-command():
            false
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        with pytest.raises(ExecutionError):
            eval(root_module, "🐭.explicit-exit()")
        # A jazzoo-mode line is its own shebang block, so it fails the same way.
        with pytest.raises(ExecutionError):
            eval(root_module, "🐭.failing-command()")


def test_a_run_time_error_aborts_the_remaining_body(tmp_path):
    """A run-time error aborts the whole run: jazzoo does not continue with the
    remaining lines of the body. Nothing is rolled back - steps that already ran
    have already had their effects."""
    if True:
        # Config
        before = tmp_path / "before.marker"
        after = tmp_path / "after.marker"

        jazzoo_fn = save_fixture(f"""# test_abort_body.jaz
        run():
            touch {before}
            false
            touch {after}
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        with pytest.raises(ExecutionError):
            eval(root_module, "🐭.run()")
        # The step before the failure ran, and its effect stands.
        assert os.path.exists(before)
        # The step after it never ran.
        assert not os.path.exists(after)


def test_a_failing_dependency_aborts_later_dependencies_and_the_body(tmp_path):
    """A run-time error in a dependency aborts the run: later dependencies do not
    run, and neither does the body of the target that triggered them."""
    if True:
        # Config
        first = tmp_path / "first.marker"
        second = tmp_path / "second.marker"
        body = tmp_path / "body.marker"

        jazzoo_fn = save_fixture(f"""# test_abort_dependencies.jaz
        [private]
        _fails():
            touch {first}
            false

        [private]
        _never-runs():
            touch {second}

        run(): \\
                _fails() \\
                _never-runs()
            touch {body}
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        with pytest.raises(ExecutionError):
            eval(root_module, "🐭.run()")
        assert os.path.exists(first)
        assert not os.path.exists(second)
        assert not os.path.exists(body)
