from config_tests.config_test_env import Context, TestEnv

from jazzoo.config import ConfigExpansionError

CONFIG_YAML = """
    env: prod
    level: env
    flag: true
    nothing: null
    primary: 1
    hosts:
      - a.example.com
      - b.example.com
    urls:
      dev: http://localhost:8000
      prod: https://shop.example.com
    api_url: ${/urls/${/env}}
    env_url: ${/urls/${SHOP_ENV}}
    deep_url: ${/urls/${/${/level}}}
    primary_host: ${/hosts/${/primary}}
    bad:
      boolean: ${/urls/${/flag}}
      none: ${/urls/${/nothing}}
      list: ${/urls/${/hosts}}
      dict: ${/urls/${/urls}}
    """


def create_env(context: Context):
    return Env(context)


def test_nested_references(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a config file with nested references.
    if env.step(
        env.set_env("SHOP_ENV", "dev"),
        env.write_config("config.yaml", CONFIG_YAML),
        env.use_config_files("config.yaml"),
    ):
        pass

    # We read the api url, which picks a url by the value of /env.
    #
    # The inner reference should be expanded first, and give the prod url.
    if env.step(
        env.get("/api_url"),
    ):
        assert env.value == "https://shop.example.com"

    # We read a url that is picked by an environment variable.
    #
    # It should give the dev url.
    if env.step(
        env.get("/env_url"),
    ):
        assert env.value == "http://localhost:8000"

    # We read a url with references nested three levels deep.
    #
    # /level gives "env", /env gives "prod", so it should give the prod url.
    if env.step(
        env.get("/deep_url"),
    ):
        assert env.value == "https://shop.example.com"

    # We read a host whose index comes from a number in the config.
    #
    # The number should be used as a list index.
    if env.step(
        env.get("/primary_host"),
    ):
        assert env.value == "b.example.com"

    # We read a value whose inner reference yields a boolean.
    #
    # A boolean cannot be part of a path, so it should raise a
    # ConfigExpansionError.
    if env.step(
        env.get_and_catch_error("/bad/boolean"),
    ):
        assert isinstance(env.error, ConfigExpansionError)

    # We read a value whose inner reference yields null.
    #
    # It should raise a ConfigExpansionError.
    if env.step(
        env.get_and_catch_error("/bad/none"),
    ):
        assert isinstance(env.error, ConfigExpansionError)

    # We read a value whose inner reference yields a list.
    #
    # It should raise a ConfigExpansionError.
    if env.step(
        env.get_and_catch_error("/bad/list"),
    ):
        assert isinstance(env.error, ConfigExpansionError)

    # We read a value whose inner reference yields a dict.
    #
    # It should raise a ConfigExpansionError.
    if env.step(
        env.get_and_catch_error("/bad/dict"),
    ):
        assert isinstance(env.error, ConfigExpansionError)


class Env(TestEnv):
    pass
