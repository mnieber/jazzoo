import os

from commands_tests.commands_test_env import Context, TestEnv

LIST_AND_STRING_SCRIPT = """
from jazzoo.commands import run

run(["echo", "two words"])
run("echo one | tr a-z A-Z")
"""

CWD_SCRIPT = """
from jazzoo.commands import run

run("pwd", cwd="sub")
"""

ECHO_SCRIPT = """
from jazzoo.commands import run

run("echo hello", echo=True)
"""

PLAIN_SCRIPT = """
from jazzoo.commands import run

run("echo hello")
"""

CAPTURE_SCRIPT = """
from jazzoo.commands import run

result = run("echo captured", capture=True)
print(repr(result.stdout), flush=True)
"""


def create_env(context: Context):
    return Env(context)


def test_confirm_prompt(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a script that runs a list command with an argument that contains a
    # space, and a string command. We switch on the confirmation of commands, and
    # run the script.
    #
    # The list command should be shown with its terms joined and quoted as in a
    # shell, and the string command as it was given. Neither command has a cwd, so
    # the prompt should show the current directory of the script.
    if env.step(
        env.write_file("list_and_string.py", LIST_AND_STRING_SCRIPT),
        env.set_env("JAZZOO_CONFIRM", "1"),
        env.run_python_script_in_pty("list_and_string.py", answers=["y", "y"]),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.prompts == [
            f"({env.path('')}) echo 'two words'",
            f"({env.path('')}) echo one | tr a-z A-Z",
        ]

    # We have a script that runs a command with a cwd. We run the script.
    #
    # The prompt should show the cwd, as it was given.
    if env.step(
        env.make_dir("sub"),
        env.write_file("cwd.py", CWD_SCRIPT),
        env.run_python_script_in_pty("cwd.py", answers=["y"]),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.prompts == ["(sub) pwd"]
        assert env.pty_lines() == [env.path("sub")]

    # We have a script that runs a command with echo. We run the script, with its
    # stdout redirected to a file.
    #
    # The prompt should replace the echo: it should appear on the terminal, and the
    # file should only hold the output of the command.
    if env.step(
        env.write_file("echo.py", ECHO_SCRIPT),
        env.run_python_script_in_pty("echo.py", answers=["y"], stdout_file="out.log"),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.prompts == [f"({env.path('')}) echo hello"]
        assert env.read_file("out.log") == "hello\n"
        assert env.pty_output == ""

    # We have a script that runs a command without echo. We run the script, with its
    # stdout redirected to a file.
    #
    # The prompt should appear on the terminal, and not in the file.
    if env.step(
        env.write_file("plain.py", PLAIN_SCRIPT),
        env.run_python_script_in_pty("plain.py", answers=["y"], stdout_file="out.log"),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.prompts == [f"({env.path('')}) echo hello"]
        assert env.read_file("out.log") == "hello\n"
        assert env.pty_output == ""

    # We have a script that captures the output of a command, and prints it. We run
    # the script.
    #
    # The prompt should still be shown, and should not be part of the captured
    # output.
    if env.step(
        env.write_file("capture.py", CAPTURE_SCRIPT),
        env.run_python_script_in_pty("capture.py", answers=["y"]),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.prompts == [f"({env.path('')}) echo captured"]
        assert env.pty_lines() == ["'captured\\n'"]


class Env(TestEnv):
    def make_dir(self, name: str):
        os.makedirs(self.path(name))
