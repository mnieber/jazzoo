from commands_tests.commands_test_env import Context, TestEnv

from jazzoo.commands import CommandFailedError


def create_env(context: Context):
    return Env(context)


def test_script_checks_exit_codes(context: Context):
    # Create the test environment
    env = create_env(context)

    # We run a command that exits with 3, and tell run not to check the exit code.
    #
    # It should return the result, with exit code 3.
    if env.step(
        env.run("exit 3", check=False),
    ):
        assert env.result.returncode == 3

    # We run the same command, with the default check.
    #
    # It should raise a CommandFailedError that holds the result, and whose message
    # names the command and the exit code.
    if env.step(
        env.run_and_catch_error("exit 3"),
    ):
        assert isinstance(env.error, CommandFailedError)
        assert env.error.result.returncode == 3
        assert "exit 3" in str(env.error)
        assert "exit code 3" in str(env.error)

    # We run a command that writes an error message to stderr and fails, and
    # capture its output.
    #
    # The message of the CommandFailedError should include the captured stderr.
    if env.step(
        env.run_and_catch_error("echo 'disk full' >&2; exit 1", capture=True),
    ):
        assert isinstance(env.error, CommandFailedError)
        assert "disk full" in str(env.error)


class Env(TestEnv):
    pass
