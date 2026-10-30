import json
import typing as T

from config_tests.config_test_env import Context, TestEnv

CONFIG_YAML = """
    shop:
      name: Jane's shop
      port: 8080
      ratio: 1.5
      debug: true
      owner: null
      tags: [web, api]
      db:
        host: ${DB_HOST}
        url: postgres://${/shop/db/host}/shop
    """


def create_env(context: Context):
    return Env(context)


def test_get_config_values(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a config file with values of every JSON type, and a jazzoo file.
    if env.step(
        env.set_env("DB_HOST", "db.internal"),
        env.write_config("config.yaml", CONFIG_YAML),
        env.use_config_files("config.yaml"),
        env.write_file("jazzoo", "noop():\n    true\n"),
        env.parse_module("jazzoo"),
    ):
        pass

    # We read the values of the shop section.
    #
    # Each should come back as the same JSON value.
    if env.step(
        env.read_config("/shop/name", store_as="name"),
        env.read_config("/shop/port", store_as="port"),
        env.read_config("/shop/ratio", store_as="ratio"),
        env.read_config("/shop/debug", store_as="debug"),
        env.read_config("/shop/owner", store_as="owner"),
        env.read_config("/shop/tags", store_as="tags"),
    ):
        assert env.name == "Jane's shop"
        assert env.port == 8080
        assert env.ratio == 1.5
        assert env.debug is True
        assert env.owner is None
        assert env.tags == ["web", "api"]

    # We read the db section.
    #
    # It should come back as an object, with the environment variable and the
    # reference expanded.
    if env.step(
        env.read_config("/shop/db", store_as="db"),
    ):
        assert env.db == {
            "host": "db.internal",
            "url": "postgres://db.internal/shop",
        }

    # We read a missing path with a default.
    #
    # It should yield the default, which can be any value, also null or false.
    if env.step(
        env.read_config("/shop/missing", default='"none"', store_as="name"),
        env.read_config("/shop/missing", default="null", store_as="owner"),
        env.read_config("/shop/missing", default="false", store_as="debug"),
    ):
        assert env.name == "none"
        assert env.owner is None
        assert env.debug is False

    # We read a path whose value is null, with a default.
    #
    # The default only covers a missing path, so it should yield null.
    if env.step(
        env.read_config("/shop/owner", default='"nobody"', store_as="owner"),
    ):
        assert env.owner is None

    # We read a missing path with a default that contains a reference.
    #
    # The default should come back as is: it is not expanded.
    if env.step(
        env.read_config("/shop/missing", default='"${/shop/name}"', store_as="name"),
    ):
        assert env.name == "${/shop/name}"


class Env(TestEnv):
    def read_config(
        self, path: str, default: T.Optional[str] = None, store_as: str = "value"
    ):
        """Reads the config value at path with ⚙️.get_config, and stores the Python
        value of its JSON text. The default is a jazzoo expression."""
        default_arg = "" if default is None else f", default={default}"
        expression = f'⚙️.get_config(path="{path}"{default_arg}) | ⚙️.json'
        self.evaluate(expression, store_as="output")
        setattr(self, store_as, json.loads(self.output))
