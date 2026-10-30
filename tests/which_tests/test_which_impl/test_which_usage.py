from which_tests.which_test_env import Context, TestEnv

from jazzoo.errors import JazzooError


def create_env(context: Context):
    return Env(context)


def test_which_usage(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the project shop.
    if env.step(
        env.write_jazzoo(),
    ):
        pass

    # We run jaz --which, without a target.
    #
    # It should raise a JazzooError, and run nothing.
    if env.step(
        env.run_jaz_and_catch_error("--which"),
    ):
        assert isinstance(env.error, JazzooError)
        assert "--which needs a target" in str(env.error)
        assert env.output == ""

    # We run jaz --which --list build.
    if env.step(
        env.run_jaz_and_catch_error("--which", "--list", "build"),
    ):
        assert isinstance(env.error, JazzooError)
        assert "--which cannot be combined with --list" in str(env.error)
        assert env.output == ""

    # We run jaz --which --list-all build.
    if env.step(
        env.run_jaz_and_catch_error("--which", "--list-all", "build"),
    ):
        assert isinstance(env.error, JazzooError)
        assert "--which cannot be combined with --list-all" in str(env.error)
        assert env.output == ""

    # We run jaz --which build mode=debug.
    #
    # Nothing runs, so the arguments have no use.
    if env.step(
        env.run_jaz_and_catch_error("--which", "build", "mode=debug"),
    ):
        assert isinstance(env.error, JazzooError)
        assert "--which takes no arguments" in str(env.error)
        assert env.output == ""

    # We run jaz --which through the console script.
    #
    # It should print the error, and exit with 1.
    if env.step(
        env.run_jaz_cli("--which"),
    ):
        assert env.exit_code == 1
        assert env.output == ""
        assert "--which needs a target" in env.printed_err


class Env(TestEnv):
    pass
