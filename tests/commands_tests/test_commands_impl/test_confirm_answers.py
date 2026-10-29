from commands_tests.commands_test_env import CTRL_D, Context, TestEnv

from jazzoo.commands import CommandAbortedError, CommandError

SCRIPT = """
from jazzoo.commands import run

run("echo ran")
print("done", flush=True)
"""


def create_env(context: Context):
    return Env(context)


def test_confirm_answers(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a script that runs one command, and then prints "done". We switch on
    # the confirmation of commands, run the script, and press Enter at the prompt.
    #
    # Enter means yes: the command should run.
    if env.step(
        env.write_file("script.py", SCRIPT),
        env.set_env("JAZZOO_CONFIRM", "1"),
        env.run_python_script_in_pty("script.py", answers=[""]),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.pty_lines() == ["ran", "done"]

    # We run the script, and answer Y.
    #
    # The answer is case-insensitive, so the command should run.
    if env.step(
        env.run_python_script_in_pty("script.py", answers=["Y"]),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.pty_lines() == ["ran", "done"]

    # We run the script, and answer " n ".
    #
    # The answer is stripped, so the command should be skipped, and the script
    # should continue.
    if env.step(
        env.run_python_script_in_pty("script.py", answers=[" n "]),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.pty_lines() == ["done"]

    # We run the script, and answer "yes", then "x", then "y".
    #
    # Only y, n, q and Enter are answers: the prompt should be shown again for the
    # same command until the answer is y, and then the command should run.
    if env.step(
        env.run_python_script_in_pty("script.py", answers=["yes", "x", "y"]),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.prompts == [f"({env.path('')}) echo ran"] * 3
        assert env.pty_lines() == ["ran", "done"]

    # We run the script, and press ctrl-d at the prompt.
    #
    # The end of input should abort the script with a CommandAbortedError, as q
    # does.
    if env.step(
        env.run_python_script_in_pty("script.py", answers=[CTRL_D]),
    ):
        assert env.exit_code != 0
        assert "CommandAbortedError" in env.pty_output
        assert "ran" not in env.pty_lines()
        assert "done" not in env.pty_lines()

    # We look at CommandAbortedError.
    #
    # It should be a CommandError, so that a script that catches the errors of run
    # also catches an abort.
    if env.step():
        assert issubclass(CommandAbortedError, CommandError)


class Env(TestEnv):
    pass
