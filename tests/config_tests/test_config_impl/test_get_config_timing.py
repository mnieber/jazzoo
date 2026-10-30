from config_tests.config_test_env import Context, TestEnv

from jazzoo import ExecutionError

TOP_LEVEL_SOURCE = """
    🐭.before = ⚙️.get_config(path="/shop/name", default="unset")
    ⚙️.load_config(path=⚙️.module.dirname / "shop.yaml")
    🐭.after = ⚙️.get_config(path="/shop/name", default="unset")
    """

INVALID_SOURCE = """
    ⚙️.load_config(path=⚙️.module.dirname / "invalid.yaml")

    hello():
        echo hello

    show():
        echo {{ ⚙️.get_config(path="/shop/name") }}
    """

FUNCTION_BODY_SOURCE = """
    ⚙️.load_config(path=⚙️.module.dirname / "shop.yaml")

    show():
        🐆.before = ⚙️.get_config(path="/shop/name")
        ⚙️.load_config(path=⚙️.module.dirname / "rename.yaml")
        echo "🐆.before -> {{ ⚙️.get_config(path="/shop/name") }}"
    """


def create_env(context: Context):
    return Env(context)


def test_get_config_timing(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a jazzoo file that reads a value at the top level, before and after
    # it loads the config file that sets it.
    #
    # The first read should not see the config file, and the second should.
    if env.step(
        env.write_config("shop.yaml", "shop:\n  name: Jane's shop\n"),
        env.write_file("top_level.jaz", TOP_LEVEL_SOURCE),
        env.parse_module("top_level.jaz"),
        env.evaluate("🐭.before", store_as="before"),
        env.evaluate("🐭.after", store_as="after"),
    ):
        assert env.before == "unset"
        assert env.after == "Jane's shop"

    # We have a jazzoo file that loads a config file that is not valid YAML.
    #
    # The file should load, and a target that does not read the config should run:
    # the config is parsed when it is first read.
    if env.step(
        env.unset_env("JAZZOO_CONFIG_FILES"),
        env.write_config("invalid.yaml", "shop: [unclosed\n"),
        env.write_file("invalid.jaz", INVALID_SOURCE),
        env.parse_module("invalid.jaz"),
        env.evaluate("🐭.hello()"),
    ):
        assert env.output == "hello"

    # We run the target that reads the config.
    #
    # It should raise an ExecutionError.
    if env.step(
        env.evaluate_and_catch_error("🐭.show()"),
    ):
        assert isinstance(env.error, ExecutionError)

    # We have a jazzoo file whose target reads a value, loads a config file that
    # overrides it, and reads it again.
    #
    # The second read should see the new value.
    if env.step(
        env.unset_env("JAZZOO_CONFIG_FILES"),
        env.write_config("rename.yaml", "shop:\n  name: Bob's shop\n"),
        env.write_file("function_body.jaz", FUNCTION_BODY_SOURCE),
        env.parse_module("function_body.jaz"),
        env.evaluate("🐭.show()"),
    ):
        assert env.output == "Jane's shop -> Bob's shop"


class Env(TestEnv):
    def __post_init__(self):
        super().__post_init__()
        self.before = None
        self.after = None
