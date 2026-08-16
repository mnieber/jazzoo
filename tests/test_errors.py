"""Cross-cutting error behaviour.

Errors specific to one topic are tested alongside that topic - argument and
execution errors in test_functions.py, pipe and curry errors in
test_pipes_and_currying.py, import errors in test_imports.py, resolution of
unset references in test_substitutions.py. What is left here is what holds
across all of them: the shared base class, the source location every error
carries, when errors are detected, and what the user sees.
"""

import pytest

from jazzoo import (
    ArgumentError,
    ExecutionError,
    JazzooError,
    ModuleImportError,
    ParseError,
    ResolutionError,
    evaluate,
    parse_module,
)
from jazzoo.runtime.entrypoints.jazzoo import main
from jazzoo.runtime.utils.test_utils import save_fixture


def test_syntax_that_does_not_parse_is_a_parse_error():
    """Syntax that does not parse is a ParseError, detected in phase 1."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bad_syntax.jaz
        debug(name="me"
            echo "never gets here"
        """)

        # Run / Assert
        with pytest.raises(ParseError):
            parse_module(jazzoo_fn)


def test_every_error_derives_from_jazzoo_error():
    """All errors jazzoo raises derive from a single base class, JazzooError."""
    if True:
        # Config
        subclasses = [
            ParseError,
            ResolutionError,
            ArgumentError,
            ModuleImportError,
            ExecutionError,
        ]

        # Assert
        for subclass in subclasses:
            assert issubclass(subclass, JazzooError)
        assert issubclass(JazzooError, Exception)


def test_no_error_shadows_a_python_builtin():
    """None of the error classes shadow a Python builtin, so they can be imported
    directly without aliasing."""
    if True:
        # Config
        import builtins

        names = [
            "JazzooError",
            "ParseError",
            "ResolutionError",
            "ArgumentError",
            "ModuleImportError",
            "ExecutionError",
        ]

        # Assert
        # `ImportError` is a builtin, which is why the import variant is spelled
        # `ModuleImportError`.
        for name in names:
            assert not hasattr(builtins, name)


def test_a_parse_time_error_carries_its_source_location():
    """Every error carries the .jaz file and 1-based line it is attributed to, so the
    message can point at the offending source rather than at jazzoo's internals."""
    if True:
        # Config
        # The bad call site is on line 6 of the fixture body: the `# <filename>`
        # directive is stripped by save_fixture, so line 1 is `build(target):`.
        jazzoo_fn = save_fixture("""# test_parse_error_location.jaz
        build(target):
            #!/usr/bin/env bash
            echo "🐆.target"

        test():
            🐭.build(profile="dev")
        """)

        # Run
        with pytest.raises(ArgumentError) as excinfo:
            parse_module(jazzoo_fn)

        # Assert
        assert excinfo.value.filename == jazzoo_fn
        assert excinfo.value.line == 6
        assert excinfo.value.message


def test_a_run_time_error_carries_its_source_location():
    """Run-time errors are attributed to a source location too - by a different code
    path than parse-time ones, since the file has long since been parsed."""
    if True:
        # Config
        # `false` is on line 3 of the fixture body.
        jazzoo_fn = save_fixture("""# test_run_error_location.jaz
        run():
            echo "fine"
            false
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        with pytest.raises(ExecutionError) as excinfo:
            evaluate(root_module, "🐭.run()")

        # Assert
        assert excinfo.value.filename == jazzoo_fn
        assert excinfo.value.line == 3
        assert excinfo.value.message


def test_an_error_is_attributed_to_the_module_that_contains_it():
    """The location points at the .jaz file the error is in, which is not necessarily
    the entry-point file."""
    if True:
        # Config
        library_fn = save_fixture("""# broken_library.jaz
        run():
            false
        """)

        jazzoo_fn = save_fixture("""# test_error_in_import.jaz
        from ./broken_library.jaz import run as lib

        go():
            🐭.lib.run()
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        with pytest.raises(ExecutionError) as excinfo:
            evaluate(root_module, "🐭.go()")

        # Assert
        # The failing line lives in the library, not in the file that called it.
        assert excinfo.value.filename == library_fn
        assert excinfo.value.line == 2


def test_parse_time_errors_fire_regardless_of_the_target_invoked():
    """Anything decidable from the parse tree alone is raised when the file is
    loaded - before any subprocess runs, and regardless of which target was invoked.
    A file with a bad call site in one target therefore fails even when a different
    target is run."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_early_detection.jaz
        healthy():
            #!/usr/bin/env bash
            echo "nothing wrong with me"

        broken():
            🐭.no-such-function()
        """)

        # Run / Assert
        # Loading fails on its own, without naming a target at all.
        with pytest.raises(ResolutionError):
            parse_module(jazzoo_fn)


def test_list_fails_on_a_file_with_a_parse_time_error(capsys):
    """`jaz --list` fails too: mistakes surface immediately rather than when some
    rarely-used branch is first exercised."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_list_fails.jaz
        healthy():
            #!/usr/bin/env bash
            echo "nothing wrong with me"

        broken():
            🐭.no-such-function()
        """)

        # Run
        exit_code = main(["--list", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        # Listing does not degrade gracefully - a broken file has no listing.
        assert exit_code != 0
        assert "healthy" not in captured.out


def test_the_user_sees_only_the_message_and_its_location(capsys):
    """By default jaz prints only the error message, prefixed with its source
    location, and exits with a non-zero status."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_error_output.jaz
        build(target):
            #!/usr/bin/env bash
            echo "🐆.target"

        test():
            🐭.build(profile="dev")
        """)

        # Run
        exit_code = main(["test", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code != 0
        # e.g. "test_error_output.jaz:6: error: build() has no parameter named 'profile'"
        assert "test_error_output.jaz:6: error: " in captured.err
        assert "profile" in captured.err


def test_a_stack_trace_is_shown_only_with_trace(capsys):
    """A stack trace is never shown without --trace - it describes jazzoo's
    internals, not the user's .jaz file. Passing --trace adds one."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_trace_flag.jaz
        run():
            false
        """)

        # Run
        without_trace_code = main(["run", "--file", jazzoo_fn])
        without_trace = capsys.readouterr()

        with_trace_code = main(["--trace", "run", "--file", jazzoo_fn])
        with_trace = capsys.readouterr()

        # Assert
        assert without_trace_code != 0
        assert with_trace_code != 0
        assert "Traceback (most recent call last)" not in without_trace.err
        assert "Traceback (most recent call last)" in with_trace.err
        # The actionable location is printed either way.
        assert "test_trace_flag.jaz:2: error: " in without_trace.err
        assert "test_trace_flag.jaz:2: error: " in with_trace.err
