from commands_tests.commands_test_env import Context, TestEnv

SCRIPT = """
from jazzoo.commands import run

run("echo ran")
"""


def create_env(context: Context):
    return Env(context)


def test_confirm_switch(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a script that runs a command. We run it in a terminal, without
    # JAZZOO_CONFIRM, and answer no prompts.
    #
    # The command should run without a prompt (an unexpected prompt fails the
    # test).
    if env.step(
        env.write_file("script.py", SCRIPT),
        env.run_python_script_in_pty("script.py"),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.pty_lines() == ["ran"]

    # We set JAZZOO_CONFIRM to 0, and run the script.
    #
    # Only 1 switches the confirmation on, so the command should run without a
    # prompt.
    if env.step(
        env.set_env("JAZZOO_CONFIRM", "0"),
        env.run_python_script_in_pty("script.py"),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.pty_lines() == ["ran"]

    # We set JAZZOO_CONFIRM to an empty string, and run the script.
    #
    # The command should run without a prompt.
    if env.step(
        env.set_env("JAZZOO_CONFIRM", ""),
        env.run_python_script_in_pty("script.py"),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.pty_lines() == ["ran"]

    # We set JAZZOO_CONFIRM to true, and run the script.
    #
    # The command should run without a prompt.
    if env.step(
        env.set_env("JAZZOO_CONFIRM", "true"),
        env.run_python_script_in_pty("script.py"),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.pty_lines() == ["ran"]

    # We set JAZZOO_CONFIRM to 1, and run the script.
    #
    # The command should be confirmed before it runs.
    if env.step(
        env.set_env("JAZZOO_CONFIRM", "1"),
        env.run_python_script_in_pty("script.py", answers=["y"]),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.prompts == [f"({env.path('')}) echo ran"]
        assert env.pty_lines() == ["ran"]


class Env(TestEnv):
    pass
