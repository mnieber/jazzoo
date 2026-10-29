from docker_tests.docker_test_env import Context, TestEnv

# Runs a command in the foreground, and a captured one
SCRIPT = """
from jazzoo import run, run_docker

run_be = run_docker("blogs_be")(run)

run_be("echo plain")
print(run_be("echo captured", capture=True).stdout, end="", flush=True)
"""

PLAIN = ["blogs_be", "bash", "-c", "echo plain"]
CAPTURED = ["blogs_be", "bash", "-c", "echo captured"]


def create_env(context: Context):
    return Env(context)


def test_tty(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a script that runs a command in the container blogs_be, and a
    # captured one. We run it in a terminal.
    #
    # The command should have been run with --interactive and --tty, so that it
    # can talk to the user. The captured command should have been run without
    # --tty, so that its output is not mixed with stderr.
    if env.step(
        env.install_fake_docker(),
        env.write_file("script.py", SCRIPT),
        env.run_python_script_in_pty("script.py"),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.pty_lines() == ["plain", "captured"]
        assert env.docker_calls() == [
            ["exec", "--interactive", "--tty", *PLAIN],
            ["exec", "--interactive", *CAPTURED],
        ]

    # We run the script in a terminal, but with its stdout redirected to a file.
    #
    # Only stdin is a terminal, so neither command should have been run with --tty.
    if env.step(
        env.forget_docker_calls(),
        env.run_python_script_in_pty("script.py", stdout_file="output.txt"),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.read_file("output.txt") == "plain\ncaptured\n"
        assert env.docker_calls() == [
            ["exec", "--interactive", *PLAIN],
            ["exec", "--interactive", *CAPTURED],
        ]

    # We run the script without a terminal, as in CI.
    #
    # Neither command should have been run with --tty, and the script should not
    # fail.
    if env.step(
        env.forget_docker_calls(),
        env.run_python_script("script.py"),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout == "plain\ncaptured\n"
        assert env.docker_calls() == [
            ["exec", "--interactive", *PLAIN],
            ["exec", "--interactive", *CAPTURED],
        ]


class Env(TestEnv):
    pass
