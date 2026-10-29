from docker_tests.docker_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_docker_client_env(context: Context):
    # Create the test environment
    env = create_env(context)

    # We decorate run with run_docker and the variable BLOGS_MODE, and run a
    # captured command that prints BLOGS_MODE and BLOGS_DEBUG, with BLOGS_DEBUG in
    # the env of the call.
    #
    # Both variables should have been set for the command in the container. They
    # should not have been set in the environment of the docker client, nor in that
    # of the script.
    if env.step(
        env.unset_env("BLOGS_MODE"),
        env.unset_env("BLOGS_DEBUG"),
        env.install_fake_docker(),
        env.decorate_run("blogs_be", env={"BLOGS_MODE": "test"}),
        env.call_decorated(
            "echo $BLOGS_MODE $BLOGS_DEBUG", env={"BLOGS_DEBUG": "1"}, capture=True
        ),
    ):
        assert env.result.stdout == "test 1\n"
        assert env.docker_client_envs() == [{"BLOGS_MODE": None, "BLOGS_DEBUG": None}]
        assert env.env_var("BLOGS_MODE") is None
        assert env.env_var("BLOGS_DEBUG") is None


class Env(TestEnv):
    pass
