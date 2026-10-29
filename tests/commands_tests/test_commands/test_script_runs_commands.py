from commands_tests.commands_test_env import Context, TestEnv

# Prints how many arguments it got, and the first one
COUNT_ARGS = "import sys; print(len(sys.argv) - 1, sys.argv[1])"

SCRIPT = f"""
import sys

from jazzoo.commands import run

run("echo one | tr a-z A-Z")
run([sys.executable, "-c", {COUNT_ARGS!r}, "two words"])
head = run("echo three", capture=True).stdout
print(f"captured: {{head.strip()}}", flush=True)
"""


def create_env(context: Context):
    return Env(context)


def test_script_runs_commands(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a Python script that runs a string command with a pipe, a list command
    # with an argument that contains a space, and a string command whose output it
    # captures and prints. We run the script.
    #
    # The string command should have run in bash, so the pipe worked. The list
    # command should have received "two words" as one argument. The captured
    # output should not have been shown, but returned to the script.
    if env.step(
        env.write_file("deploy.py", SCRIPT),
        env.run_python_script("deploy.py"),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout == "ONE\n1 two words\ncaptured: three\n"


class Env(TestEnv):
    pass
