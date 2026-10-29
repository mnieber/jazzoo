from commands_tests.commands_test_env import Context, TestEnv

# Runs commands with invalid arguments, and prints the type of each error
INVALID_ARGUMENTS_SCRIPT = """
from jazzoo.commands import run

for command, kwargs in [
    ("   ", {}),
    ([], {}),
    ("true", {"cwd": "missing"}),
    (["no-such-executable-xyz"], {}),
]:
    try:
        run(command, **kwargs)
    except Exception as error:
        print(type(error).__name__, flush=True)
"""

NO_TERMINAL_SCRIPT = """
from jazzoo.commands import CommandError, run

try:
    run("touch ran.txt")
except CommandError as error:
    print(type(error).__name__, error, flush=True)
"""


def create_env(context: Context):
    return Env(context)


def test_confirm_errors(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a script that runs an empty string command, an empty list command, a
    # command with a missing cwd, and an unknown executable. We switch on the
    # confirmation of commands, and run the script in a terminal.
    #
    # The arguments are checked before the prompt, so each call should raise its
    # usual error without a prompt (an unexpected prompt fails the test).
    if env.step(
        env.write_file("invalid_arguments.py", INVALID_ARGUMENTS_SCRIPT),
        env.set_env("JAZZOO_CONFIRM", "1"),
        env.run_python_script_in_pty("invalid_arguments.py"),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.pty_lines() == [
            "ValueError",
            "ValueError",
            "ValueError",
            "CommandNotFoundError",
        ]

    # We have a script that runs a command. We run it without a controlling
    # terminal.
    #
    # run cannot ask, so it should raise a CommandError that says that a terminal is
    # needed, and the command should not run.
    if env.step(
        env.write_file("no_terminal.py", NO_TERMINAL_SCRIPT),
        env.run_python_script("no_terminal.py"),
    ):
        assert env.completed.stdout == "CommandError --confirm needs a terminal\n"
        assert not env.file_exists("ran.txt")


class Env(TestEnv):
    pass
