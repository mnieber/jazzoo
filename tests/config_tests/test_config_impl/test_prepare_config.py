from config_tests.config_test_env import Context, TestEnv

from jazzoo.config import ConfigFileError

CONFIG_YAML = """
    root:
      user: ${SHOP_USER}
      token: ${SHOP_UNSET_TOKEN}
    """


def create_env(context: Context):
    return Env(context)


def test_prepare_config(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a config file with a user from the environment, and a token from an
    # environment variable that is not set. We call prepare_config.
    #
    # It should return None, and not fail on the token, because it expands
    # nothing.
    if env.step(
        env.set_env("SHOP_USER", "jane"),
        env.unset_env("SHOP_UNSET_TOKEN"),
        env.write_config("config.yaml", CONFIG_YAML),
        env.use_config_files("config.yaml"),
        env.prepare_config(),
    ):
        assert env.value is None

    # We change the user in the environment, and call prepare_config again.
    #
    # The cache for this list of files exists, so it should not take a new copy of
    # the environment.
    if env.step(
        env.set_env("SHOP_USER", "john"),
        env.prepare_config(),
    ):
        pass

    # We read the user for the first time.
    #
    # It should be the user from the copy that the first prepare_config took.
    if env.step(
        env.get("/root/user"),
    ):
        assert env.value == "jane"

    # We have a config file with a syntax error, and call prepare_config.
    #
    # It should raise a ConfigFileError.
    if env.step(
        env.write_config("broken.yaml", "root:\n  src: /src: oops\n"),
        env.use_config_files("broken.yaml"),
        env.prepare_config_and_catch_error(),
    ):
        assert isinstance(env.error, ConfigFileError)


class Env(TestEnv):
    pass
