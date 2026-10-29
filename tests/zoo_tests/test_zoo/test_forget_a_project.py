from zoo_tests.zoo_test_env import Context, TestEnv

from jazzoo.zoo.errors import NoSuchZooEnvError


def create_env(context: Context):
    return Env(context)


def test_forget_a_project(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the registered projects "shop" and "blog".
    if env.step(
        env.add_project("shop"),
        env.init_env("shop"),
        env.add_project("blog"),
        env.init_env("blog"),
    ):
        pass

    # We forget shop.
    #
    # Its directory in the registry and its zoo-shop link should be gone. The
    # project and the venv should still be there, and zoo should say on stderr
    # that it did not remove the venv. Nothing should be printed to source.
    if env.step(
        env.run_zoo("env", "--forget", "shop"),
    ):
        assert not env.exists(env.env_dir("shop"))
        assert not env.exists(env.zoo_link("shop"))
        assert env.is_dir(env.path("projects/shop"))
        assert env.is_dir(env.path("projects/shop/.venv"))
        assert env.output == ""
        assert env.printed_err == (
            'Forgot zoo environment "shop". Its venv was not removed: '
            + env.path("projects/shop/.venv")
            + "\n"
        )

    # We list the envs.
    #
    # Only blog should be left.
    if env.step(
        env.run_zoo("env", "--list"),
    ):
        assert env.output.splitlines() == ["  blog  " + env.path("projects/blog")]

    # We try to activate shop.
    #
    # It is no longer registered, so this should raise a NoSuchZooEnvError.
    if env.step(
        env.run_zoo_and_catch_error("env", "shop"),
    ):
        assert isinstance(env.error, NoSuchZooEnvError)
        assert env.error.message == "no such zoo environment: shop"


class Env(TestEnv):
    pass
