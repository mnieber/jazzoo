import sys

from interactive_tests.interactive_test_env import Context, TestEnv

# The same Python block, once in an interactive target and once in a captured one.
# The block prints, starts a command that reports whether its stdout is a terminal,
# and prints again.
BLOCK = f"""
    #!{sys.executable}
    from jazzoo.commands import run

    print("step 1")
    run("echo step 2; [ -t 1 ] && echo tty || echo no-tty")
    print("step 3")
"""

JAZZOO_SOURCE = (
    """
[interactive]
live():"""
    + BLOCK
    + """
captured():"""
    + BLOCK
)


def create_env(context: Context):
    return Env(context)


def test_interactive_target_uses_the_terminal(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a jazzoo file with an interactive target and a captured target, which
    # run the same Python block. We run the interactive target in a terminal.
    #
    # The block should see the terminal: the command reports a terminal on its
    # stdout. The output of the script and of its command should appear in the order
    # in which it was written.
    if env.step(
        env.write_file("jazzoo", JAZZOO_SOURCE),
        env.run_jaz_in_pty("live"),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.pty_lines() == ["step 1", "step 2", "tty", "step 3"]

    # We run the captured target in a terminal.
    #
    # Its block should not see the terminal, because its output is captured.
    if env.step(
        env.run_jaz_in_pty("captured"),
    ):
        assert env.exit_code == 0, env.pty_output
        assert "no-tty" in env.pty_lines()
        assert "tty" not in env.pty_lines()


class Env(TestEnv):
    pass
