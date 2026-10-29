import subprocess
import sys

from commands_tests.commands_test_env import Context, TestEnv

from jazzoo.commands.entrypoints.jaz_run import main, run as run_jaz_run
from jazzoo.commands.errors import UsageError


def create_env(context: Context):
    return Env(context)


def test_jaz_run_exit_codes(context: Context):
    # Create the test environment
    env = create_env(context)

    # We run jaz-run with a command that succeeds.
    #
    # It should exit with 0, and print nothing on stderr.
    if env.step(
        env.run_jaz_run_cli("-c", "exit 0"),
        env.read_printed(),
    ):
        assert env.exit_code == 0
        assert env.printed_err == ""

    # We run jaz-run with a command that writes to stderr, and exits with 3.
    #
    # jaz-run should exit with the exit code of the command, and add no message of
    # its own: the stderr of the command is already visible.
    if env.step(
        env.run_jaz_run_cli("-c", "echo oops >&2; exit 3"),
        env.read_printed(),
    ):
        assert env.exit_code == 3
        assert env.printed_err == "oops\n"

    # We run jaz-run with an unknown executable.
    #
    # It should exit with 127, as a shell does, and print the message of the
    # CommandNotFoundError.
    if env.step(
        env.run_jaz_run_cli("no-such-executable-xyz"),
        env.read_printed(),
    ):
        assert env.exit_code == 127
        assert env.printed_err == "jaz-run: command not found: no-such-executable-xyz\n"

    # We run jaz-run without arguments.
    #
    # This is a usage error: it should exit with 2, with a message on stderr.
    if env.step(
        env.run_jaz_run_cli(),
        env.read_printed(),
    ):
        assert env.exit_code == 2
        assert env.printed_err.startswith("jaz-run: ")

    # We run jaz-run with -c, but without a command.
    #
    # This is a usage error.
    if env.step(
        env.run_jaz_run_cli("-c"),
        env.read_printed(),
    ):
        assert env.exit_code == 2
        assert env.printed_err.startswith("jaz-run: ")

    # We run jaz-run with -c and two arguments.
    #
    # A string command is a single argument, so this is a usage error.
    if env.step(
        env.run_jaz_run_cli("-c", "echo one", "echo two"),
        env.read_printed(),
    ):
        assert env.exit_code == 2
        assert env.printed_err.startswith("jaz-run: ")
        assert env.printed == ""

    # We run jaz-run with an unknown option before the command.
    #
    # This is a usage error, and the command should not run.
    if env.step(
        env.run_jaz_run_cli("--bogus", "echo", "hi"),
        env.read_printed(),
    ):
        assert env.exit_code == 2
        assert env.printed_err.startswith("jaz-run: ")
        assert env.printed == ""

    # We call the run function of jaz-run with an unknown option.
    #
    # It should raise a UsageError, so that the error can be inspected.
    if env.step(
        env.run_jaz_run_and_catch_error("--bogus", "echo", "hi"),
    ):
        assert isinstance(env.error, UsageError)

    # We run jaz-run with an empty string command.
    #
    # This is an error of run itself: it should exit with 2, with the message of
    # run.
    if env.step(
        env.run_jaz_run_cli("-c", ""),
        env.read_printed(),
    ):
        assert env.exit_code == 2
        assert env.printed_err == "jaz-run: the command is empty\n"

    # We switch on the confirmation of commands, and run jaz-run without a
    # controlling terminal.
    #
    # It should exit with 2, say that a terminal is needed, and not run the
    # command.
    if env.step(
        env.set_env("JAZZOO_CONFIRM", "1"),
        env.run_jaz_run_without_terminal("-c", "touch ran.txt"),
    ):
        assert env.completed.returncode == 2
        assert env.completed.stderr == "jaz-run: --confirm needs a terminal\n"
        assert not env.file_exists("ran.txt")


class Env(TestEnv):
    def run_jaz_run_cli(self, *args: str):
        self.exit_code = main(list(args))

    def run_jaz_run_and_catch_error(self, *args: str):
        self.error = None
        try:
            run_jaz_run(list(args))
        except Exception as error:
            self.error = error

    def run_jaz_run_without_terminal(self, *args: str):
        """Runs jaz-run in a new session, which has no controlling terminal."""
        self.completed = subprocess.run(
            [sys.executable, "-m", "jazzoo.commands", *args],
            cwd=self.path(""),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            start_new_session=True,
            timeout=30,
        )
