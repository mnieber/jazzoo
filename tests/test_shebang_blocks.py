import pytest

from jazzoo import evaluate, parse_module
from jazzoo.runtime.utils.test_utils import save_fixture

pytestmark = pytest.mark.stage(1)


def test_each_jazzoo_mode_line_is_its_own_subprocess():
    """In the default jazzoo execution mode, every line runs in its own shell
    shebang block - so nothing carries over from one line to the next."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_line_isolation.jaz
        working-directory():
            cd /tmp
            pwd

        shell-variables():
            FOO=bar
            echo "[$FOO]"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # The `cd` affected only its own subprocess, so `pwd` runs where the target
        # started - anywhere but /tmp.
        assert evaluate(root_module, "🐭.working-directory()") != "/tmp"
        # FOO was set in a shell that then exited.
        assert evaluate(root_module, "🐭.shell-variables()") == "[]"

    """Use an explicit shebang block whenever lines need to share state: it is one
    subprocess, so the cd applies."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_block_shares_state.jaz
        working-directory():
            #!/usr/bin/env bash
            cd /tmp
            pwd

        shell-variables():
            #!/usr/bin/env bash
            FOO=bar
            echo "[$FOO]"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.working-directory()") == "/tmp"
        assert evaluate(root_module, "🐭.shell-variables()") == "[bar]"


def test_the_default_mode_is_equivalent_to_per_line_bash_blocks():
    """A body in the default mode is equivalent to the same lines written as one
    bash shebang block each."""
    if True:
        # Config
        implicit_fn = save_fixture("""# test_implicit_mode.jaz
        help():
            echo "hello"
            echo "world"
        """)

        explicit_fn = save_fixture("""# test_explicit_mode.jaz
        help():
            #!/usr/bin/env bash
            echo "hello"

            #!/usr/bin/env bash
            echo "world"
        """)

        # Run
        implicit_module = parse_module(implicit_fn)
        explicit_module = parse_module(explicit_fn)

        # Assert
        assert evaluate(implicit_module, "🐭.help()") == evaluate(
            explicit_module, "🐭.help()"
        )


def test_an_alternative_interpreter_runs_the_block():
    """A function body can use a shebang block to run an alternative interpreter."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_alternative_interpreter.jaz
        🐭.tracing = "on"

        help():
            #!/usr/bin/env python3
            print("Tracing is: 🐭.tracing, fyi")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.help()") == "Tracing is: on, fyi"


def test_a_bare_shebang_returns_to_the_default_mode():
    """A bare `#!` means the previous shebang block ended and we return to the
    default jazzoo execution mode."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bare_shebang.jaz
        help():
            #!/usr/bin/env python3
            print("from python")

            #!
            echo "back in jazzoo mode"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.help()") == "back in jazzoo mode"


def test_stdout_captures_the_last_block_and_output_strips_the_newline():
    """⚙️.stdout captures what the last shebang block in the current function wrote
    to stdout. ⚙️.output equals ⚙️.stdout minus the trailing newline, if it has one."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_stdout_and_output.jaz
        raw():
            #!/usr/bin/env bash
            echo "Test"

            #!
            🐆.retval = "[⚙️.stdout]"

        trimmed():
            #!/usr/bin/env bash
            echo "Test"

            #!
            🐆.retval = "[⚙️.output]"

        without_a_trailing_newline():
            #!/usr/bin/env bash
            printf 'Test'

            #!
            🐆.retval = "[⚙️.output]"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.raw()") == "[Test\n]"
        assert evaluate(root_module, "🐭.trimmed()") == "[Test]"
        # Only a trailing newline is removed - there is nothing to strip here.
        assert evaluate(root_module, "🐭.without_a_trailing_newline()") == "[Test]"


def test_each_block_replaces_the_previous_stdout():
    """⚙️.stdout is the stdout of the *last* block, so each block replaces what the
    one before it left behind."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_stdout_replaced.jaz
        help():
            #!/usr/bin/env python3
            print("Tracing is: on, fyi")

            #!
            echo "We just wrote ⚙️.output"
            echo "Test"
            echo "Last message was: ⚙️.output"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # Each jazzoo-mode line is its own block, so by the last line ⚙️.output is
        # what the line before it echoed.
        assert evaluate(root_module, "🐭.help()") == "Last message was: Test"


def test_stdout_is_not_affected_by_calls_to_other_functions():
    """The value of ⚙️.stdout is not affected by calls to other jazzoo functions -
    it is local to the function whose body is running."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_stdout_is_local.jaz
        [private]
        _noisy():
            #!/usr/bin/env bash
            echo "callee output"

        help():
            #!/usr/bin/env bash
            echo "caller output"

            #!
            🐭._noisy()
            🐆.retval = "⚙️.output"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # The callee's echo did not overwrite the caller's ⚙️.stdout.
        assert evaluate(root_module, "🐭.help()") == "caller output"


def test_sweeping_extracts_assignments_and_substitutes_references():
    """Before execution jazzoo sweeps the block top to bottom: jazzoo assignments are
    evaluated and removed, and all references in the remaining lines are substituted
    using the namespace state at that point. The block then runs as one subprocess."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_sweeping.jaz
        info():
            #!/usr/bin/env python3
            🐆.config = "hello.json"

            print("first: 🐆.config")

            🐆.config = "bye.json"

            print("second: 🐆.config")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # Each print sees the value assigned above it, and the assignment lines
        # themselves are gone from the Python that runs.
        assert (
            evaluate(root_module, "🐭.info()") == "first: hello.json\nsecond: bye.json"
        )


def test_a_swept_assignment_outlives_its_block():
    """Sweeping updates the namespace, so a value assigned inside one block is still
    the current value in the next one."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_assignment_outlives_block.jaz
        info():
            #!/usr/bin/env python3
            🐆.config = "hello.json"
            print("🐆.config")

            🐆.config = "bye.json"
            print("🐆.config")

            #!/usr/bin/env bash
            echo "The 🐆.config file was used in our Python shebang block"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # The bash block sees the last value the Python block's sweep assigned.
        assert (
            evaluate(root_module, "🐭.info()")
            == "The bye.json file was used in our Python shebang block"
        )


def test_indentation_does_not_affect_whether_a_line_is_an_assignment():
    """Trimming determines whether a line is a jazzoo assignment, so indentation makes
    no difference - an assignment inside a Python for loop is still extracted."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_indented_assignment.jaz
        info():
            #!/usr/bin/env python3
            for i in range(3):
                🐆.config = "in-loop.json"
                print("🐆.config")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # The assignment was extracted rather than executed three times, so the
        # substitution is static: the loop only prints the value.
        assert (
            evaluate(root_module, "🐭.info()")
            == "in-loop.json\nin-loop.json\nin-loop.json"
        )


def test_a_braced_reference_passes_through_the_sweep():
    """A braced reference is not a leading sigil, so it passes through the sweep as a
    regular line rather than being extracted as an assignment."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_braced_not_extracted.jaz
        🐭.variable = "foo"

        info():
            #!/usr/bin/env python3
            {{ 🐭.variable }} = "bar"
            print(foo)
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # `foo = "bar"` survived into the Python that ran.
        assert evaluate(root_module, "🐭.info()") == "bar"
