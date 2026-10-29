import typing as T

from docker_tests.docker_test_env import Context, TestEnv

from jazzoo.commands import run_docker

DOCKER_EXEC = ["docker", "exec", "--interactive"]


def create_env(context: Context):
    return Env(context)


def test_stacked_decorators(context: Context):
    # Create the test environment
    env = create_env(context)

    # We decorate the recording function with a logging decorator, and decorate the
    # result with run_docker. We call it.
    #
    # The logging decorator is below run_docker, so it should have seen the docker
    # exec command.
    if env.step(
        env.decorate_logging_recorder_with_run_docker("blogs_be"),
        env.call_decorated(["pytest"]),
    ):
        assert env.logged_commands == [DOCKER_EXEC + ["blogs_be", "pytest"]]
        assert env.last_recorded_command() == DOCKER_EXEC + ["blogs_be", "pytest"]

    # We decorate the recording function with run_docker, and decorate the result
    # with the logging decorator. We call it.
    #
    # The logging decorator is above run_docker, so it should have seen the command
    # as it was given. The recording function should still receive the docker exec
    # command.
    if env.step(
        env.forget_logged_commands(),
        env.decorate_recorder_with_run_docker_and_logging("blogs_be"),
        env.call_decorated(["pytest"]),
    ):
        assert env.logged_commands == [["pytest"]]
        assert env.last_recorded_command() == DOCKER_EXEC + ["blogs_be", "pytest"]


class Env(TestEnv):
    def decorate_logging_recorder_with_run_docker(self, container: str):
        self.decorated = run_docker(container)(self._logging(self._record))

    def decorate_recorder_with_run_docker_and_logging(self, container: str):
        self.decorated = self._logging(run_docker(container)(self._record))

    def forget_logged_commands(self):
        self.logged_commands = []

    def _logging(self, f: T.Callable) -> T.Callable:
        def logging_f(command, *args, **kwargs):
            self.logged_commands.append(command)
            return f(command, *args, **kwargs)

        return logging_f
