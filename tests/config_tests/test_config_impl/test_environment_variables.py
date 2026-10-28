from config_tests.config_test_env import Context, TestEnv

from jazzoo.config import ConfigExpansionError

CONFIG_YAML = """
    db:
      host: ${SHOP_DB_HOST}
      user_unset: ${SHOP_DB_USER_UNSET:-postgres}
      user_empty: ${SHOP_DB_USER_EMPTY:-postgres}
      user_set: ${SHOP_DB_USER_SET:-postgres}
    missing: ${SHOP_UNSET_VARIABLE}
    shell: echo $HOME
    escaped: $${HOME}
    escaped_ref: $${/db/host}
    keys:
      "${/db/host}": 1
    """


def create_env(context: Context):
    return Env(context)


def test_environment_variables(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a config file that uses environment variables.
    if env.step(
        env.set_env("SHOP_DB_HOST", "db.internal"),
        env.unset_env("SHOP_DB_USER_UNSET"),
        env.set_env("SHOP_DB_USER_EMPTY", ""),
        env.set_env("SHOP_DB_USER_SET", "jane"),
        env.unset_env("SHOP_UNSET_VARIABLE"),
        env.write_config("config.yaml", CONFIG_YAML),
        env.use_config_files("config.yaml"),
    ):
        pass

    # We read the database settings.
    #
    # ${NAME} should give the variable. ${NAME:-default} should give the default
    # when the variable is unset or empty, and the variable when it is set.
    if env.step(
        env.get("/db"),
    ):
        assert env.value == {
            "host": "db.internal",
            "user_unset": "postgres",
            "user_empty": "postgres",
            "user_set": "jane",
        }

    # We read a value that uses an unset variable without a default.
    #
    # It should raise a ConfigExpansionError that names the variable and the path
    # of the value.
    if env.step(
        env.get_and_catch_error("/missing"),
    ):
        assert isinstance(env.error, ConfigExpansionError)
        assert "SHOP_UNSET_VARIABLE" in str(env.error)
        assert "/missing" in str(env.error)

    # We read a shell snippet that uses $HOME without braces.
    #
    # It should stay literal text.
    if env.step(
        env.get("/shell"),
    ):
        assert env.value == "echo $HOME"

    # We read values that are escaped with $${.
    #
    # They should yield a literal ${, for an environment variable and for a
    # reference alike.
    if env.step(
        env.get("/escaped", store_as="escaped"),
        env.get("/escaped_ref", store_as="escaped_ref"),
    ):
        assert env.escaped == "${HOME}"
        assert env.escaped_ref == "${/db/host}"

    # We read a dict with a key that looks like a reference.
    #
    # Keys are never expanded.
    if env.step(
        env.get("/keys"),
    ):
        assert env.value == {"${/db/host}": 1}


class Env(TestEnv):
    def __post_init__(self):
        super().__post_init__()
        self.escaped = None
        self.escaped_ref = None
