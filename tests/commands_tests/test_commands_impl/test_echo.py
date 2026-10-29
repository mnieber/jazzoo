import shlex
import sys

from commands_tests.commands_test_env import Context, TestEnv

from jazzoo.commands import CommandFailedError

COUNT_ARGS = [sys.executable, "-c", "import sys; print(len(sys.argv) - 1)", "two words"]
EXIT_4 = [sys.executable, "-c", "raise SystemExit(4)"]


def create_env(context: Context):
    return Env(context)


def test_echo(context: Context):
    # Create the test environment
    env = create_env(context)

    # We run a command.
    #
    # By default, the command should not be echoed: only its output is printed.
    if env.step(
        env.run("echo hello"),
        env.read_printed(),
    ):
        assert env.printed == "hello\n"

    # We run a string command with echo.
    #
    # The command should be printed as it was given, before its output.
    if env.step(
        env.run("echo hello", echo=True),
        env.read_printed(),
    ):
        assert env.printed == "echo hello\nhello\n"

    # We run a list command with echo, with an argument that contains a space.
    #
    # The command should be printed with its terms joined and quoted as in a shell.
    if env.step(
        env.run(COUNT_ARGS, echo=True),
        env.read_printed(),
    ):
        assert env.printed == shlex.join(COUNT_ARGS) + "\n1\n"

    # We run a command with echo and a working directory.
    #
    # The working directory should be printed before the command.
    if env.step(
        env.run("echo hello", echo=True, cwd=env.path("")),
        env.read_printed(),
    ):
        assert env.printed == f"({env.path('')}) echo hello\nhello\n"

    # We run a failing list command with a working directory.
    #
    # The CommandFailedError should show the command in the same way.
    if env.step(
        env.run_and_catch_error(EXIT_4, cwd=env.path("")),
    ):
        assert isinstance(env.error, CommandFailedError)
        assert f"({env.path('')}) {shlex.join(EXIT_4)}" in str(env.error)


class Env(TestEnv):
    pass
