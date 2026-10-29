import sys

from confirm_tests.confirm_test_env import Context, TestEnv

# The Python block of build is captured, as every block of a function that is not
# interactive. show-version calls version quietly.
JAZZOO_SOURCE = f"""
build():
    #!{sys.executable}
    from jazzoo.commands import run

    run("echo built")

[private]
_version():
    #!{sys.executable}
    from jazzoo.commands import run

    run("echo 1.2.3")

show-version():
    🐆.version = 🐭._version()
    @echo "version=🐆.version"
"""


def create_env(context: Context):
    return Env(context)


def test_confirm_reaches_the_terminal(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a jazzoo file with a target whose Python block runs a command. The
    # output of the block is captured by jaz. We run the target with --confirm in a
    # terminal.
    #
    # The prompt should reach the terminal, although the output of the block is
    # captured. The output of the command should be printed by jaz.
    if env.step(
        env.write_file("jazzoo", JAZZOO_SOURCE),
        env.run_jaz_in_pty("--confirm", "build", answers=["y"]),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.prompts == [f"({env.path('')}) echo built"]
        assert env.pty_lines() == ["built"]

    # We run a target that calls a function quietly, and prints its value. The
    # function runs a command.
    #
    # The prompt should reach the terminal, although the call is quiet. The output
    # of the command should be the value of the call.
    if env.step(
        env.run_jaz_in_pty("--confirm", "show-version", answers=["y"]),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.prompts == [f"({env.path('')}) echo 1.2.3"]
        assert env.pty_lines() == ["version=1.2.3"]

    # We run jaz --confirm build with the output of jaz redirected to a file.
    #
    # The prompt should reach the terminal, and should not be in the file. The
    # output of the command should be in the file.
    if env.step(
        env.run_jaz_in_pty(
            "--confirm", "build", answers=["y"], stdout_file="build.log"
        ),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.prompts == [f"({env.path('')}) echo built"]
        assert env.read_file("build.log") == "built\n"
        assert env.pty_output == ""


class Env(TestEnv):
    pass
