import sys

from confirm_tests.confirm_test_env import Context, TestEnv

INNER_SOURCE = f"""
build():
    #!{sys.executable}
    from jazzoo.commands import run

    run("echo inner-built")
"""

JAZZOO_SOURCE = """
outer():
    @jaz --file inner.jaz build

stop():
    @jaz-run -c "echo never"
    @echo after
"""


def create_env(context: Context):
    return Env(context)


def test_confirm_nesting(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a jazzoo file whose outer target runs a nested jaz, without
    # --confirm. The target of the nested jaz runs a command with run. We run jaz
    # --confirm outer in a terminal.
    #
    # The nested jaz inherits JAZZOO_CONFIRM, so its command should be confirmed.
    if env.step(
        env.write_file("inner.jaz", INNER_SOURCE),
        env.write_file("jazzoo", JAZZOO_SOURCE),
        env.run_jaz_in_pty("--confirm", "outer", answers=["y"]),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.prompts == [f"({env.path('')}) echo inner-built"]
        assert "inner-built" in env.pty_lines()

    # We run jaz --confirm stop, whose first line runs a command with jaz-run, and
    # answer q.
    #
    # jaz-run should exit with 130, so the shell line fails, and jaz should stop the
    # run: the next line never runs.
    if env.step(
        env.run_jaz_in_pty("--confirm", "stop", answers=["q"]),
    ):
        assert env.exit_code != 0
        assert "jaz-run: aborted by the user" in env.pty_output
        assert "never" not in env.pty_lines()
        assert "after" not in env.pty_lines()


class Env(TestEnv):
    pass
