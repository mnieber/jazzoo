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


def test_a_shebang_blocks_body_is_not_echoed(capfd):
    """A jazzoo-mode line is echoed before it runs, but a shebang block is not: its
    swept body is a script, not a command, and only its output is shown."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_shebang_not_echoed.jaz
        go(name="jane"):
            #!/usr/bin/env python3
            greeting = "hello"
            print(greeting + " 🐆.name")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        retval = evaluate(root_module, "🐭.go()")
        captured = capfd.readouterr()

        # Assert
        assert "hello jane" in captured.out
        assert "greeting" not in captured.out
        assert "#!/usr/bin/env python3" not in captured.out
        assert retval == "hello jane"


def test_a_call_whose_value_is_used_runs_quietly(capfd):
    """When a call's return value is used - assigned, piped, passed as an operand
    or substituted inline - the call is quiet: neither its commands nor their
    output reach the console. Its value is unaffected."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_captured_call_is_quiet.jaz
        [private]
        _config():
            echo '{"host": "captured-host"}'

        assigned():
            🐆.retval = 🐭._config()

        piped():
            🐆.config = 🐭._config() | ⚙️.parse
            🐆.retval = 🐆.config.host

        operand():
            🐆.retval = 🐭._config() or "fallback"

        inline():
            @echo "length:" $(echo '🐭._config()' | wc -c)
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        assigned = evaluate(root_module, "🐭.assigned()")
        piped = evaluate(root_module, "🐭.piped()")
        operand = evaluate(root_module, "🐭.operand()")
        inline = evaluate(root_module, "🐭.inline()")
        captured = capfd.readouterr()

        # Assert
        assert assigned == '{"host": "captured-host"}'
        assert piped == "captured-host"
        assert operand == '{"host": "captured-host"}'
        assert inline.startswith("length:")
        assert "captured-host" not in captured.out
        assert "captured-host" not in captured.err


def test_a_call_used_as_a_statement_still_prints(capfd):
    """A call whose value is not used - a mid-body call on its own line, or a
    dependency - prints its commands and their output, like a target does."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_statement_call_prints.jaz
        [private]
        _step(name):
            echo "step 🐆.name ran"

        go(): _step(name="dependency")
            🐭._step(name="mid-body")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        evaluate(root_module, "🐭.go()")
        captured = capfd.readouterr()

        # Assert
        assert 'echo "step dependency ran"' in captured.out
        assert 'echo "step mid-body ran"' in captured.out
        assert "\nstep mid-body ran\n" in captured.out


def test_a_quiet_call_is_quiet_all_the_way_down(capfd):
    """Quietness covers everything a captured call runs, including the functions
    that it calls as statements."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_quiet_call_nested.jaz
        [private]
        _inner():
            echo "inner-output"

        [private]
        _outer():
            🐭._inner()
            echo "outer-output"

        go():
            🐆.retval = 🐭._outer()
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        retval = evaluate(root_module, "🐭.go()")
        captured = capfd.readouterr()

        # Assert
        assert retval == "outer-output"
        assert "inner-output" not in captured.out
        assert "outer-output" not in captured.out


def test_a_quiet_call_still_shows_stderr(capfd):
    """Only stdout is held back. A quiet call's stderr still reaches the console,
    so its warnings and errors stay visible."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_quiet_call_stderr.jaz
        [private]
        _value():
            @echo "a warning" >&2
            @echo "the-value"

        go():
            🐆.retval = 🐭._value()
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        retval = evaluate(root_module, "🐭.go()")
        captured = capfd.readouterr()

        # Assert
        assert retval == "the-value"
        assert "a warning" in captured.err
        assert "the-value" not in captured.out


def test_a_module_level_call_runs_quietly(capfd):
    """A module-level assignment is evaluated whenever the module is loaded - also
    for `jaz --list` - so a call on its right-hand side is quiet as well."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_module_level_call_quiet.jaz
        [private]
        _host-ip():
            echo "10.1.2.3"

        🐐.host-ip = 🐭._host-ip()

        show():
            @echo "ip is 🐐.host-ip"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        load_output = capfd.readouterr()
        retval = evaluate(root_module, "🐭.show()")

        # Assert
        assert "10.1.2.3" not in load_output.out
        assert retval == "ip is 10.1.2.3"
