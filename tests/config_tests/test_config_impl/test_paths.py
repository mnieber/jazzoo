import typing as T

from config_tests.config_test_env import Context, TestEnv

from jazzoo.config import ConfigKeyError

CONFIG_YAML = """
    root:
      src: /home/jane/projects/shop/src
      tags:
        - web
        - api
    """


def create_env(context: Context):
    return Env(context)


def test_paths(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a config file with a source dir and a list of tags.
    if env.step(
        env.write_config("config.yaml", CONFIG_YAML),
        env.use_config_files("config.yaml"),
    ):
        pass

    # We read a key that does not exist.
    #
    # It should raise a ConfigKeyError that names the path and the first segment
    # that was not found.
    if env.step(
        env.get_and_catch_error("/root/database/host"),
    ):
        assert isinstance(env.error, ConfigKeyError)
        assert "/root/database/host" in str(env.error)
        assert "database" in str(env.error)

    # We read past the end of the list of tags.
    #
    # It should raise a ConfigKeyError.
    if env.step(
        env.get_and_catch_error("/root/tags/2"),
    ):
        assert isinstance(env.error, ConfigKeyError)

    # We use a segment that is not a number to index the list of tags.
    #
    # It should raise a ConfigKeyError.
    if env.step(
        env.get_and_catch_error("/root/tags/first"),
    ):
        assert isinstance(env.error, ConfigKeyError)

    # We read a key inside the source dir, which is a string.
    #
    # It should raise a ConfigKeyError.
    if env.step(
        env.get_and_catch_error("/root/src/name"),
    ):
        assert isinstance(env.error, ConfigKeyError)

    # We read missing keys with a default.
    #
    # It should return the default, as is: a default that looks like a reference
    # is not expanded.
    if env.step(
        env.get("/root/database", default={"host": "localhost"}),
        env.get("/root/home", default="${HOME}", store_as="home"),
    ):
        assert env.value == {"host": "localhost"}
        assert env.home == "${HOME}"

    # We read the root section with and without a trailing slash.
    #
    # Both should give the same result.
    if env.step(
        env.get("/root/"),
        env.get("/root", store_as="root"),
    ):
        assert env.value == env.root
        assert env.root["src"] == "/home/jane/projects/shop/src"

    # We use a path without a leading slash.
    #
    # It should raise a ValueError.
    if env.step(
        env.get_and_catch_error("root/src"),
    ):
        assert isinstance(env.error, ValueError)

    # We use a path without a leading slash, with a default.
    #
    # The default does not apply to a malformed path: it should still raise a
    # ValueError.
    if env.step(
        env.get_and_catch_error("root/src", default="/src"),
    ):
        assert isinstance(env.error, ValueError)


class Env(TestEnv):
    def __post_init__(self):
        super().__post_init__()
        self.home: T.Any = None
        self.root: T.Any = None
