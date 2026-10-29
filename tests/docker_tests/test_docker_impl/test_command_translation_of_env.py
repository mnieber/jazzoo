from docker_tests.docker_test_env import Context, TestEnv

DOCKER_EXEC = ["docker", "exec", "--interactive"]


def create_env(context: Context):
    return Env(context)


def test_command_translation_of_env(context: Context):
    # Create the test environment
    env = create_env(context)

    # We decorate the recording function with run_docker and two variables, and
    # call it with an env that overrides one of them and adds another one.
    #
    # The variables should be passed with --env: those of run_docker first, where
    # the call overrides a variable in its place, followed by the new one of the
    # call. The function should have received no env.
    if env.step(
        env.decorate_recorder("blogs_be", env={"DEBUG": "0", "LANG": "C"}),
        env.call_decorated(["env"], env={"DEBUG": "1", "TZ": "UTC"}),
    ):
        assert env.last_recorded_command() == DOCKER_EXEC + [
            "--env",
            "DEBUG=1",
            "--env",
            "LANG=C",
            "--env",
            "TZ=UTC",
            "blogs_be",
            "env",
        ]
        assert env.recorded_calls[-1]["env"] is None

    # We call it again without an env.
    #
    # The override only applied to the earlier call: the variables of run_docker
    # should be passed unchanged.
    if env.step(
        env.call_decorated(["env"]),
    ):
        assert env.last_recorded_command() == DOCKER_EXEC + [
            "--env",
            "DEBUG=0",
            "--env",
            "LANG=C",
            "blogs_be",
            "env",
        ]

    # We decorate it with a user, a working directory and a variable, and call it.
    #
    # The options should come in the fixed order: --user, --workdir, --env.
    if env.step(
        env.decorate_recorder(
            "blogs_be", env={"DEBUG": "1"}, workdir="/app", user="app"
        ),
        env.call_decorated(["env"]),
    ):
        assert env.last_recorded_command() == DOCKER_EXEC + [
            "--user",
            "app",
            "--workdir",
            "/app",
            "--env",
            "DEBUG=1",
            "blogs_be",
            "env",
        ]


class Env(TestEnv):
    pass
