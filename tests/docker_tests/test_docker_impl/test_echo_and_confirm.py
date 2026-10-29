import shlex

from docker_tests.docker_test_env import Context, TestEnv

# Runs a command that is skipped, and prints its result, and then one that runs
SCRIPT = """
from jazzoo import run, run_docker

run_be = run_docker("blogs_be")(run)

result = run_be(["touch", "made.txt"])
print("skipped", result.skipped, flush=True)
run_be("echo ran")
"""


def create_env(context: Context):
    return Env(context)


def test_echo_and_confirm(context: Context):
    # Create the test environment
    env = create_env(context)

    # We decorate run with run_docker for the container blogs_be and the app
    # directory, and run a command with echo.
    #
    # The echo should show the full docker exec command, because that is what
    # runs, followed by the output of the command. The result should hold the
    # docker exec command as well.
    if env.step(
        env.install_fake_docker(),
        env.make_dir("app"),
        env.decorate_run("blogs_be", workdir=env.path("app")),
        env.call_decorated(["echo", "tested"], echo=True),
        env.read_printed(),
    ):
        docker_exec = ["docker", "exec", "--interactive", "--workdir", env.path("app")]
        assert env.printed == (
            shlex.join(docker_exec + ["blogs_be", "echo", "tested"]) + "\ntested\n"
        )
        assert env.result.command == docker_exec + ["blogs_be", "echo", "tested"]

    # We have a script that runs two commands in the container. We switch on the
    # confirmation of commands, run the script in a terminal, skip the first
    # command and run the second.
    #
    # The prompts should show the full docker exec commands, after the current
    # directory on the host. The skipped command should not have reached docker,
    # so only the second command should have been run, and the result of the
    # first should say that it was skipped.
    if env.step(
        env.forget_docker_calls(),
        env.write_file("script.py", SCRIPT),
        env.set_env("JAZZOO_CONFIRM", "1"),
        env.run_python_script_in_pty("script.py", answers=["n", "y"]),
    ):
        assert env.exit_code == 0, env.pty_output
        docker_exec = ["docker", "exec", "--interactive", "--tty", "blogs_be"]
        assert env.prompts == [
            f"({env.path('')}) " + shlex.join(docker_exec + ["touch", "made.txt"]),
            f"({env.path('')}) " + shlex.join(docker_exec + ["bash", "-c", "echo ran"]),
        ]
        assert not env.file_exists("made.txt")
        assert env.docker_calls() == [docker_exec[1:] + ["bash", "-c", "echo ran"]]
        assert env.pty_lines() == ["skipped True", "ran"]


class Env(TestEnv):
    pass
