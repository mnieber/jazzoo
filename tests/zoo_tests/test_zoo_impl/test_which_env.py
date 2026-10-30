from zoo_tests.zoo_test_env import Context, TestEnv

from jazzoo.errors import JazzooError
from jazzoo.zoo.errors import NoSuchZooEnvError


def create_env(context: Context):
    return Env(context)


def test_which_env(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the registered project shop.
    if env.step(
        env.add_project("shop"),
        env.init_env("shop"),
    ):
        pass

    # We set JAZZOO_ENV to the empty string, and run zoo --which.
    #
    # An empty JAZZOO_ENV means that no env is active.
    if env.step(
        env.set_env("JAZZOO_ENV", ""),
        env.run_zoo("--which"),
    ):
        assert env.exit_code == 0
        assert env.output == ""

    # We activate shop, but run a zoo whose venv belongs to no env.
    #
    # zoo --which only reads the active env, so it should still print shop.
    if env.step(
        env.set_env("JAZZOO_ENV", "shop"),
        env.make_dir("elsewhere"),
        env.use_zoo_of("elsewhere"),
        env.run_zoo("--which"),
    ):
        assert env.exit_code == 0
        assert env.output.splitlines() == ["shop  " + env.path("projects/shop")]

    # We remove the venv of shop, and run zoo --which.
    #
    # The line should say what is missing, as in zoo env --list.
    if env.step(
        env.remove_dir("projects/shop/.venv"),
        env.run_zoo("--which"),
    ):
        assert env.output.splitlines() == [
            "shop  " + env.path("projects/shop") + " (venv missing)"
        ]

    # We remove the project directory of shop, and run zoo --which.
    if env.step(
        env.change_dir("elsewhere"),
        env.remove_dir("projects/shop"),
        env.run_zoo("--which"),
    ):
        assert env.output.splitlines() == [
            "shop  " + env.path("projects/shop") + " (root dir missing)"
        ]

    # We set JAZZOO_ENV to gone, which is not registered, and run zoo --which.
    #
    # It should raise a NoSuchZooEnvError.
    if env.step(
        env.set_env("JAZZOO_ENV", "gone"),
        env.run_zoo_and_catch_error("--which"),
    ):
        assert isinstance(env.error, NoSuchZooEnvError)
        assert "no such zoo environment: gone" in str(env.error)
        assert env.output == ""

    # We run zoo --which through the console script.
    #
    # It should print the error, and exit with 1.
    if env.step(
        env.run_zoo_cli("--which"),
    ):
        assert env.exit_code == 1
        assert env.output == ""
        assert "zoo: error: no such zoo environment: gone" in env.printed_err

    # We run zoo --which --list.
    #
    # As with jaz, --which cannot be combined with --list.
    if env.step(
        env.run_zoo_and_catch_error("--which", "--list"),
    ):
        assert isinstance(env.error, JazzooError)
        assert "--which cannot be combined with --list" in str(env.error)
        assert env.output == ""

    # We run zoo --which --list-all.
    if env.step(
        env.run_zoo_and_catch_error("--which", "--list-all"),
    ):
        assert isinstance(env.error, JazzooError)
        assert "--which cannot be combined with --list-all" in str(env.error)
        assert env.output == ""


class Env(TestEnv):
    pass
