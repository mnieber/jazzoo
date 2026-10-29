import sys

from commands_tests.commands_test_env import Context, TestEnv

# Reads a line from stdin through a captured command, and prints it
READ_STDIN_SCRIPT = """
from jazzoo.commands import run

result = run("read line; echo got $line", capture=True)
print(result.stdout, end="")
"""


def create_env(context: Context):
    return Env(context)


def test_capture_and_result(context: Context):
    # Create the test environment
    env = create_env(context)

    # We run a command that writes to stdout and stderr.
    #
    # Its output should appear on the console, and the result should hold no
    # output.
    if env.step(
        env.run("echo building; echo warning >&2"),
        env.read_printed(),
    ):
        assert env.printed == "building\n"
        assert env.printed_err == "warning\n"
        assert env.result.stdout is None
        assert env.result.stderr is None

    # We run the same command, and capture its output.
    #
    # Nothing should appear on the console, and the result should hold both
    # outputs as text.
    if env.step(
        env.run("echo building; echo warning >&2", capture=True),
        env.read_printed(),
    ):
        assert env.printed == ""
        assert env.printed_err == ""
        assert env.result.stdout == "building\n"
        assert env.result.stderr == "warning\n"

    # We look at the command of the result.
    #
    # It should be the command as it was given to run.
    if env.step():
        assert env.result.command == "echo building; echo warning >&2"

    # We run a list command.
    #
    # The command of the result should be the list.
    if env.step(
        env.run([sys.executable, "-c", "pass"]),
    ):
        assert env.result.command == [sys.executable, "-c", "pass"]

    # We have a script that captures a command that reads a line from stdin. We run
    # the script, and feed it a line.
    #
    # The captured command should still read the stdin of the script.
    if env.step(
        env.write_file("read_stdin.py", READ_STDIN_SCRIPT),
        env.run_python_script("read_stdin.py", input="hello\n"),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout == "got hello\n"


class Env(TestEnv):
    pass
