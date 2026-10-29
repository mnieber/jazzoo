from zoo_tests.zoo_test_env import Context, TestEnv

from jazzoo.zoo.errors import NoRecentZooEnvError, NoSuchZooEnvError


def create_env(context: Context):
    return Env(context)


def test_recent_envs(context: Context):
    # Create the test environment
    env = create_env(context)

    # We go to the previous env, and to the latest env, of an empty registry.
    #
    # There are none, so both should raise a NoRecentZooEnvError.
    if env.step(
        env.run_zoo_and_catch_error("env", "-"),
    ):
        assert isinstance(env.error, NoRecentZooEnvError)
        assert env.error.message == "there is no previous zoo environment"

    if env.step(
        env.run_zoo_and_catch_error("env", "--latest"),
    ):
        assert isinstance(env.error, NoRecentZooEnvError)

    # We register the projects shop and blog.
    #
    # --init prints the line that activates the new env, so blog should be the
    # latest env, and shop the previous one.
    if env.step(
        env.add_project("shop"),
        env.init_env("shop"),
        env.add_project("blog"),
        env.init_env("blog"),
    ):
        assert env.read_recent() == {"latest": "blog", "previous": "shop"}

    # We activate blog again.
    #
    # blog is already the latest env, so it should not become the previous one.
    if env.step(
        env.run_zoo("env", "blog"),
    ):
        assert env.read_recent() == {"latest": "blog", "previous": "shop"}

    # We activate an env that does not exist.
    #
    # This should raise a NoSuchZooEnvError, and leave the recent envs alone.
    if env.step(
        env.run_zoo_and_catch_error("env", "wiki"),
    ):
        assert isinstance(env.error, NoSuchZooEnvError)
        assert env.read_recent() == {"latest": "blog", "previous": "shop"}

    # We forget blog, and go to the latest env.
    #
    # The latest env was forgotten, so this should raise a NoRecentZooEnvError.
    if env.step(
        env.run_zoo("env", "--forget", "blog"),
        env.run_zoo_and_catch_error("env", "--latest"),
    ):
        assert isinstance(env.error, NoRecentZooEnvError)


class Env(TestEnv):
    pass
