from config_tests.config_test_env import Context, TestEnv

from jazzoo import ArgumentError, ExecutionError

CONFIG_YAML = """
    shop:
      db:
        host: ${SHOP_UNSET_HOST}
      released: 2026-10-30
      ports:
        8080: web
    """


def create_env(context: Context):
    return Env(context)


def test_get_config_errors(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a config file, and a jazzoo file.
    if env.step(
        env.unset_env("SHOP_UNSET_HOST"),
        env.write_config("config.yaml", CONFIG_YAML),
        env.use_config_files("config.yaml"),
        env.write_file("jazzoo", "noop():\n    true\n"),
        env.parse_module("jazzoo"),
    ):
        pass

    # We read a missing path without a default.
    #
    # It should raise an ExecutionError that names the path and the segment that
    # was not found.
    if env.step(
        env.evaluate_and_catch_error('⚙️.get_config(path="/shop/name")'),
    ):
        assert isinstance(env.error, ExecutionError)
        assert "/shop/name" in str(env.error)
        assert "'name'" in str(env.error)

    # We read a path that does not start with a slash.
    #
    # It should raise an ExecutionError that names the path.
    if env.step(
        env.evaluate_and_catch_error('⚙️.get_config(path="shop/db")'),
    ):
        assert isinstance(env.error, ExecutionError)
        assert "shop/db" in str(env.error)

    # We read a value that uses an unset environment variable.
    #
    # It should raise an ExecutionError that names the variable.
    if env.step(
        env.evaluate_and_catch_error('⚙️.get_config(path="/shop/db/host")'),
    ):
        assert isinstance(env.error, ExecutionError)
        assert "SHOP_UNSET_HOST" in str(env.error)

    # We read a date, and a dict with a number as a key.
    #
    # These are not JSON values, so each should raise an ExecutionError that names
    # the path.
    if env.step(
        env.evaluate_and_catch_error('⚙️.get_config(path="/shop/released")'),
    ):
        assert isinstance(env.error, ExecutionError)
        assert "/shop/released" in str(env.error)

    if env.step(
        env.evaluate_and_catch_error('⚙️.get_config(path="/shop/ports")'),
    ):
        assert isinstance(env.error, ExecutionError)
        assert "/shop/ports" in str(env.error)

    # We load a jazzoo file that calls ⚙️.get_config without a path, and one that
    # passes an unknown parameter.
    #
    # Each should fail to load with an ArgumentError.
    if env.step(
        env.write_file("no_path.jaz", "show():\n    echo {{ ⚙️.get_config() }}\n"),
        env.parse_module_and_catch_error("no_path.jaz"),
    ):
        assert isinstance(env.error, ArgumentError)

    if env.step(
        env.write_file(
            "unknown.jaz",
            'show():\n    echo {{ ⚙️.get_config(path="/shop", fallback=1) }}\n',
        ),
        env.parse_module_and_catch_error("unknown.jaz"),
    ):
        assert isinstance(env.error, ArgumentError)


class Env(TestEnv):
    pass
