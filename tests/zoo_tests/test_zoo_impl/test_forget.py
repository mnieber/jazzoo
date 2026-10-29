import os

from zoo_tests.zoo_test_env import Context, TestEnv

from jazzoo.zoo.errors import NoSuchZooEnvError


def create_env(context: Context):
    return Env(context)


def test_forget(context: Context):
    # Create the test environment
    env = create_env(context)

    # We register the projects shop and blog, and activate shop.
    if env.step(
        env.add_project("shop"),
        env.init_env("shop"),
        env.add_project("blog"),
        env.init_env("blog"),
        env.run_zoo("env", "shop"),
    ):
        assert env.read_recent()["latest"] == "shop"

    # We point the zoo-blog link somewhere else, and forget blog.
    #
    # The link is no longer the one that zoo created, so it should be left alone.
    if env.step(
        env.replace_link(env.zoo_link("blog"), env.path("my-zoo")),
        env.run_zoo("env", "--forget", "blog"),
    ):
        assert not env.exists(env.env_dir("blog"))
        assert env.read_link(env.zoo_link("blog")) == env.path("my-zoo")

    # We forget shop, which is the latest env.
    #
    # It should no longer be the latest env.
    if env.step(
        env.run_zoo("env", "--forget", "shop"),
    ):
        assert env.read_recent().get("latest") is None

    # We forget an env that is not registered.
    #
    # This should raise a NoSuchZooEnvError.
    if env.step(
        env.run_zoo_and_catch_error("env", "--forget", "wiki"),
    ):
        assert isinstance(env.error, NoSuchZooEnvError)


class Env(TestEnv):
    def replace_link(self, path: str, target: str):
        os.remove(path)
        os.symlink(target, path)
