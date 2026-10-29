import sys

from commands_tests.commands_test_env import Context, TestEnv

from jazzoo.commands.entrypoints.jaz_run import main

# Prints the arguments that it received
PRINT_ARGS = "import sys; print(sys.argv[1:])"


def create_env(context: Context):
    return Env(context)


def test_jaz_run_arguments(context: Context):
    # Create the test environment
    env = create_env(context)

    # We run jaz-run with a list command and an option of that command.
    #
    # The options of jaz-run end where the command starts, so --echo should be
    # passed to the command, and not echo the command.
    if env.step(
        env.run_jaz_run_cli("echo", "--echo"),
        env.read_printed(),
    ):
        assert env.exit_code == 0
        assert env.printed == "--echo\n"

    # We run jaz-run with --echo and a list command.
    #
    # The command should be echoed before its output.
    if env.step(
        env.run_jaz_run_cli("--echo", "echo", "hello"),
        env.read_printed(),
    ):
        assert env.exit_code == 0
        assert env.printed == "echo hello\nhello\n"

    # We run jaz-run with --, followed by a list command whose arguments include
    # --echo, -c and an argument with a space.
    #
    # The -- should end the options of jaz-run, and every argument after the
    # executable should reach the command unchanged.
    if env.step(
        env.run_jaz_run_cli(
            "--", sys.executable, "-c", PRINT_ARGS, "--echo", "-c", "two words"
        ),
        env.read_printed(),
    ):
        assert env.exit_code == 0
        assert env.printed == "['--echo', '-c', 'two words']\n"

    # We run jaz-run with a list command that has -- as an argument.
    #
    # The -- belongs to the command, because the command has started.
    if env.step(
        env.run_jaz_run_cli("echo", "--", "hi"),
        env.read_printed(),
    ):
        assert env.exit_code == 0
        assert env.printed == "-- hi\n"

    # We run jaz-run with -c and a command with a pipe.
    #
    # The command should run in bash.
    if env.step(
        env.run_jaz_run_cli("-c", "echo one | tr a-z A-Z"),
        env.read_printed(),
    ):
        assert env.exit_code == 0
        assert env.printed == "ONE\n"

    # We run jaz-run with --echo and -c.
    #
    # The string command should be echoed as it was given.
    if env.step(
        env.run_jaz_run_cli("--echo", "-c", "echo hi"),
        env.read_printed(),
    ):
        assert env.exit_code == 0
        assert env.printed == "echo hi\nhi\n"

    # We run jaz-run with --help.
    #
    # It should print its usage, and exit with 0.
    if env.step(
        env.run_jaz_run_cli("--help"),
        env.read_printed(),
    ):
        assert env.exit_code == 0
        assert "usage" in env.printed.lower()
        assert "jaz-run" in env.printed


class Env(TestEnv):
    def run_jaz_run_cli(self, *args: str):
        self.exit_code = main(list(args))
