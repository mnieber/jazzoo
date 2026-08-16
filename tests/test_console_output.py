"""What a target actually prints to the console.

The spec-tests assert on `captured.out` after running a target, but every one of
their fixtures echoes text that also appears in the *command* jazzoo prints. They
therefore pass whether or not the command's own output reaches the console. These
tests use `@` to hide the command, so only real output can satisfy them.
"""

from jazzoo import evaluate, parse_module
from jazzoo.runtime.utils.test_utils import save_fixture


def test_a_commands_output_reaches_the_console(capsys):
    """A block's stdout is forwarded to the console, not only captured for
    ⚙️.stdout."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_output_reaches_console.jaz
        quiet():
            @echo "the real output"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        retval = evaluate(root_module, "🐭.quiet()")
        captured = capsys.readouterr()

        # Assert
        # `@` hides the echoed command, so this can only come from the subprocess.
        assert "echo" not in captured.out
        assert "the real output" in captured.out
        # And it is still captured as the return value.
        assert retval == "the real output"


def test_output_and_command_both_appear_without_the_marker(capsys):
    """Without `@`, the console shows the command and then what it printed."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_command_then_output.jaz
        loud():
            echo "hello there"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        evaluate(root_module, "🐭.loud()")
        captured = capsys.readouterr()

        # Assert
        # The command line first, then the command's own output.
        assert 'echo "hello there"' in captured.out
        command_at = captured.out.index('echo "hello there"')
        output_at = captured.out.index("hello there", command_at + 1)
        assert output_at > command_at


def test_a_shebang_blocks_output_reaches_the_console(capsys):
    """An alternative interpreter's output is forwarded the same way."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_shebang_output_console.jaz
        go():
            #!/usr/bin/env python3
            print("from python")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        evaluate(root_module, "🐭.go()")
        captured = capsys.readouterr()

        # Assert
        assert "from python" in captured.out
