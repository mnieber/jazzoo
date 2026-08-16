import os

import pytest

from jazzoo import (
    ArgumentError,
    ExecutionError,
    ParseError,
    ResolutionError,
    evaluate,
    get_function_by_path,
    get_targets,
    parse_module,
)
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
        assert evaluate(root_module, '🐭.build(target="myapp")') == "myapp-release"
        assert (
            evaluate(root_module, '🐭.build(target="myapp", mode="debug")')
            == "myapp-debug"
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
            evaluate(root_module, '🐭._helper(name="anonymous")')
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
        assert evaluate(root_module, "🐭.debug()") == "Internal helper: anonymous"


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
        assert evaluate(root_module, "🐭.deploy()") == "building myapp"


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
            evaluate(root_module, '🐭.debug(name="jane")') == "Running debug for: jane"
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
        assert evaluate(root_module, "🐭.debug()") == "high on me!"


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
            evaluate(root_module, '🐭.make-full-path(input="input.json")')
            == "/data/input.json"
        )
        # Only the last step's output survives - the first one was overwritten.
        assert evaluate(root_module, "🐭.two-steps()") == "second"


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
        assert evaluate(root_module, "🐭.from-bash()") == "/etc/jazzoo.conf"
        assert evaluate(root_module, "🐭.from-python()") == "/etc/jazzoo.conf"


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
        assert evaluate(root_module, "🐭.speak()") == "one\ntwo"
        assert evaluate(root_module, "🐭.check()") == "one\ntwo\n"


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
            evaluate(root_module, '🐭.make-full-path(input="input.json")')
            == "/data/input.json"
        )
        assert evaluate(root_module, "🐭.keep-earlier-output()") == "the value I want"


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
        assert evaluate(root_module, "🐭.debug()") == "own value"


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
        assert evaluate(root_module, "🐭.debug()") == "mine"


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
            evaluate(root_module, '🐭.help(who="jane")') == "Hello jane! / outer output"
        )


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
            evaluate(root_module, "🐭.explicit-exit()")
        # A jazzoo-mode line is its own shebang block, so it fails the same way.
        with pytest.raises(ExecutionError):
            evaluate(root_module, "🐭.failing-command()")


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
            evaluate(root_module, "🐭.run()")
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
            evaluate(root_module, "🐭.run()")
        assert os.path.exists(first)
        assert not os.path.exists(second)
        assert not os.path.exists(body)


def test_a_name_may_not_be_both_a_variable_and_a_function():
    """A reference names only a sigil and a name, so it does not say whether to look
    in a scope's variables or its functions. A scope may not define both under the
    same name."""
    if True:
        # Config
        variable_first = save_fixture("""# test_variable_then_function.jaz
        🐭.foo = "bar"

        foo():
            echo "hello"
        """)

        function_first = save_fixture("""# test_function_then_variable.jaz
        foo():
            echo "hello"

        🐭.foo = "bar"
        """)

        # Run / Assert
        # The collision is an error in either order.
        with pytest.raises(ParseError):
            parse_module(variable_first)
        with pytest.raises(ParseError):
            parse_module(function_first)


def test_a_curried_function_may_not_shadow_an_existing_name():
    """A curry expression assigns a function to a variable, so it collides with an
    existing function of the same name like any other assignment would."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_curry_name_collision.jaz
        build(target, mode="release"):
            echo "🐆.target/🐆.mode"

        🐭.build = 🐭.build[mode="dev"]
        """)

        # Run / Assert
        with pytest.raises(ParseError):
            parse_module(jazzoo_fn)

    """Under a different name it is fine - that is the ordinary currying form."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_curry_distinct_name.jaz
        build(target, mode="release"):
            echo "🐆.target/🐆.mode"

        🐭.build-in-dev = 🐭.build[mode="dev"]

        go():
            🐆.retval = 🐭.build-in-dev(target="myapp")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "myapp/dev"


def test_two_functions_may_not_share_a_name():
    """Two functions in one scope may not share a name either - the same ambiguity."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_duplicate_function.jaz
        foo():
            echo "first"

        foo():
            echo "second"
        """)

        # Run / Assert
        with pytest.raises(ParseError):
            parse_module(jazzoo_fn)


def test_the_uniqueness_rule_applies_per_scope():
    """The rule applies per scope, so a local 🐆.foo may shadow a module-level 🐭.foo -
    they are different scopes, and their sigils tell them apart."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_scope_shadowing.jaz
        🐭.foo = "module"

        go():
            🐆.foo = "local"
            🐆.retval = "🐭.foo/🐆.foo"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "module/local"

    """An imported namespace is its own scope, so it does not collide either."""
    if True:
        # Config
        save_fixture("""# name_library.jaz
        build(target):
            echo "library: 🐆.target"
        """)

        jazzoo_fn = save_fixture("""# test_namespace_no_collision.jaz
        from ./name_library.jaz import build as docker

        build(target):
            echo "own: 🐆.target"

        go():
            🐆.own = 🐭.build(target="a")
            🐆.imported = 🐭.docker.build(target="b")
            🐆.retval = "🐆.own/🐆.imported"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "own: a/library: b"
