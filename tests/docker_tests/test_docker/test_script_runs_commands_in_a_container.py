import sys

from docker_tests.docker_test_env import Context, TestEnv

# Prints how many arguments it got, and the first one
COUNT_ARGS = "import sys; print(len(sys.argv) - 1, sys.argv[1])"

SCRIPT = """
import sys

from jazzoo import run, run_docker

run_be = run_docker("blogs_be", workdir={app_dir!r})(run)

run_be("echo one | tr a-z A-Z")
run_be([sys.executable, "-c", {count_args!r}, "two words"])
workdir = run_be("pwd", capture=True).stdout
print(f"captured: {{workdir.strip()}}", flush=True)
run("echo on the host")
"""


def create_env(context: Context):
    return Env(context)


def test_script_runs_commands_in_a_container(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a container blogs_be whose working directory is the app directory.
    # A Python script decorates run with run_docker for this container. With the
    # decorated function, it runs a string command with a pipe, a list command with
    # an argument that contains a space, and a captured command whose output it
    # prints. Then it runs a command with the undecorated run. We run the script.
    #
    # The output should be that of the commands. The decorated commands should have
    # been run with docker exec in the app directory of the container: the string
    # command in bash, and the list command with "two words" as one argument. The
    # command of the undecorated run should have run on the host, without docker.
    if env.step(
        env.install_fake_docker(),
        env.make_dir("app"),
        env.write_file(
            "deploy.py",
            SCRIPT.format(app_dir=env.path("app"), count_args=COUNT_ARGS),
        ),
        env.run_python_script("deploy.py"),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout == (
            f"ONE\n1 two words\ncaptured: {env.path('app')}\non the host\n"
        )
        workdir = ["--workdir", env.path("app")]
        assert env.docker_calls() == [
            ["exec", "--interactive", *workdir, "blogs_be"]
            + ["bash", "-c", "echo one | tr a-z A-Z"],
            ["exec", "--interactive", *workdir, "blogs_be"]
            + [sys.executable, "-c", COUNT_ARGS, "two words"],
            ["exec", "--interactive", *workdir, "blogs_be", "bash", "-c", "pwd"],
        ]


class Env(TestEnv):
    pass
