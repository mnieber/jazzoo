import shlex

from docker_tests.docker_test_env import Context, TestEnv

from jazzoo.commands import CommandFailedError, CommandNotFoundError

DAEMON_MESSAGE = "Error response from daemon: container stopped is not running"


def create_env(context: Context):
    return Env(context)


def test_docker_errors(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have no docker on the PATH. We decorate run with run_docker, and run a
    # command.
    #
    # The decorated run should not find docker, and raise a CommandNotFoundError.
    if env.step(
        env.remove_docker_from_path(),
        env.decorate_run("blogs_be"),
        env.call_decorated_and_catch_error("echo hi"),
    ):
        assert isinstance(env.error, CommandNotFoundError)

    # We install docker, and run a captured command in a container that is not
    # running.
    #
    # Docker should report it, so a CommandFailedError should be raised that names
    # the docker exec command, the exit code and the message of docker.
    if env.step(
        env.install_fake_docker(),
        env.decorate_run("stopped"),
        env.call_decorated_and_catch_error("echo hi", capture=True),
    ):
        assert isinstance(env.error, CommandFailedError)
        assert env.error.result.returncode == 1
        command = [
            "docker",
            "exec",
            "--interactive",
            "stopped",
            "bash",
            "-c",
            "echo hi",
        ]
        assert shlex.join(command) in str(env.error)
        assert "exit code 1" in str(env.error)
        assert DAEMON_MESSAGE in str(env.error)

    # We run the command again with check=False.
    #
    # The result should be returned, with the exit code and the message of docker.
    if env.step(
        env.call_decorated("echo hi", capture=True, check=False),
    ):
        assert env.result.returncode == 1
        assert DAEMON_MESSAGE in env.result.stderr

    # We run a command in a running container that exits with 3.
    #
    # A CommandFailedError should be raised with the exit code of the command.
    if env.step(
        env.decorate_run("blogs_be"),
        env.call_decorated_and_catch_error("exit 3"),
    ):
        assert isinstance(env.error, CommandFailedError)
        assert env.error.result.returncode == 3


class Env(TestEnv):
    pass
