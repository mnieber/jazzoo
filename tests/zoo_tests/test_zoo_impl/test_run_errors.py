from zoo_tests.zoo_test_env import Context, TestEnv

from jazzoo.zoo.errors import NotInZooEnvError, RootDirMissingError

BROKEN_JAZZOO = """
build():
    echo 🐭.nope
"""


def create_env(context: Context):
    return Env(context)


def test_run_errors(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the registered project shop, with its venv outside the project
    # directory.
    if env.step(
        env.write_project("shop"),
        env.make_fake_venv("venvs/shop"),
        env.init_env("shop", venv="venvs/shop"),
        env.make_dir("elsewhere"),
    ):
        pass

    # We run a target with a zoo whose venv belongs to no env.
    #
    # zoo cannot know which project to use, so this should raise a
    # NotInZooEnvError.
    if env.step(
        env.make_fake_venv("venvs/other"),
        env.use_zoo_of("venvs/other"),
        env.change_dir("elsewhere"),
        env.run_zoo_and_catch_error("where"),
    ):
        assert isinstance(env.error, NotInZooEnvError)
        assert env.error.message == (
            f"not in a zoo environment (venv: {env.path('venvs/other')}); "
            "activate one with `zoo env <name>`"
        )

    # We do the same as the console script does.
    #
    # zoo should print the error, and exit with 1.
    if env.step(
        env.run_zoo_cli("where"),
    ):
        assert env.exit_code == 1
        assert env.printed_err == (
            f"zoo: error: not in a zoo environment (venv: {env.path('venvs/other')}); "
            "activate one with `zoo env <name>`\n"
        )

    # With the same zoo, we list the envs.
    #
    # zoo env does not need an env, so this should work.
    if env.step(
        env.run_zoo("env", "--list"),
    ):
        assert env.output.splitlines() == ["  shop  " + env.path("projects/shop")]

    # We remove the project directory of shop, and run a target with the zoo of
    # shop.
    #
    # This should raise a RootDirMissingError.
    if env.step(
        env.remove_dir("projects/shop"),
        env.use_zoo_of("venvs/shop"),
        env.run_zoo_and_catch_error("where"),
    ):
        assert isinstance(env.error, RootDirMissingError)

    # We write the project directory of shop again, with an error in its jazzoo
    # file, and run its target as the console script does.
    #
    # The error should be printed as jaz prints it.
    if env.step(
        env.write_project("shop", BROKEN_JAZZOO),
        env.run_zoo_cli("build"),
    ):
        assert env.exit_code == 1
        assert env.printed_err == "jazzoo:2: error: 🐭.nope is not defined\n"


class Env(TestEnv):
    pass
