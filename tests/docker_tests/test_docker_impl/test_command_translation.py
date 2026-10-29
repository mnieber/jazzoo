from docker_tests.docker_test_env import Context, TestEnv

DOCKER_EXEC = ["docker", "exec", "--interactive"]


def create_env(context: Context):
    return Env(context)


def test_command_translation(context: Context):
    # Create the test environment
    env = create_env(context)

    # We decorate a function that records its calls with run_docker for the
    # container blogs_be, and call it with a string command that has a pipe.
    #
    # The function should have received a list command: docker exec, the container,
    # and the string command, run in bash. It should have received no cwd and no
    # env, because both belong to the container.
    if env.step(
        env.decorate_recorder("blogs_be"),
        env.call_decorated("echo hi | tr a-z A-Z"),
    ):
        assert env.recorded_calls[-1]["command"] == DOCKER_EXEC + [
            "blogs_be",
            "bash",
            "-c",
            "echo hi | tr a-z A-Z",
        ]
        assert env.recorded_calls[-1]["cwd"] is None
        assert env.recorded_calls[-1]["env"] is None

    # We decorate the function for a container without bash, with shell="sh", and
    # call it with a string command.
    #
    # The string command should run in sh.
    if env.step(
        env.decorate_recorder("alpine_box", shell="sh"),
        env.call_decorated("echo hi"),
    ):
        assert env.last_recorded_command() == DOCKER_EXEC + [
            "alpine_box",
            "sh",
            "-c",
            "echo hi",
        ]

    # We decorate the function for blogs_be again, and call it with a list command
    # with an argument that contains a space.
    #
    # The list command should follow the container as it is, without a shell.
    if env.step(
        env.decorate_recorder("blogs_be"),
        env.call_decorated(["pytest", "-k", "two words"]),
    ):
        assert env.last_recorded_command() == DOCKER_EXEC + [
            "blogs_be",
            "pytest",
            "-k",
            "two words",
        ]

    # We decorate the function with a user and a working directory, and call it.
    #
    # The user and the working directory should be passed with --user and
    # --workdir, in that order, after --interactive.
    if env.step(
        env.decorate_recorder("blogs_be", user="app", workdir="/app"),
        env.call_decorated(["whoami"]),
    ):
        assert env.last_recorded_command() == DOCKER_EXEC + [
            "--user",
            "app",
            "--workdir",
            "/app",
            "blogs_be",
            "whoami",
        ]

    # We call it with a cwd, which only exists in the container.
    #
    # The cwd should replace the working directory of run_docker. It should not be
    # checked on the host, and the function should have received no cwd.
    if env.step(
        env.call_decorated(["pytest"], cwd="/app/src"),
    ):
        assert env.last_recorded_command() == DOCKER_EXEC + [
            "--user",
            "app",
            "--workdir",
            "/app/src",
            "blogs_be",
            "pytest",
        ]
        assert env.recorded_calls[-1]["cwd"] is None

    # We call it again without a cwd.
    #
    # The cwd only applied to the earlier call: the working directory of
    # run_docker should be used again.
    if env.step(
        env.call_decorated(["pytest"]),
    ):
        assert env.last_recorded_command() == DOCKER_EXEC + [
            "--user",
            "app",
            "--workdir",
            "/app",
            "blogs_be",
            "pytest",
        ]


class Env(TestEnv):
    pass
