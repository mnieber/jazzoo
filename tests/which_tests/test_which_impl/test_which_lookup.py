from which_tests.which_test_env import Context, TestEnv

from jazzoo.errors import JazzooError

ALIASES = """
[alias]
fb = fe.build mode=debug
"""


def create_env(context: Context):
    return Env(context)


def test_which_lookup(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the project shop, and the alias fb for fe.build.
    if env.step(
        env.write_jazzoo(),
        env.write_aliases(ALIASES),
    ):
        pass

    # We run jaz --which fe.lint.
    #
    # lint is defined in fe/lint.jaz, exported by fe/fe.jaz, and exported again
    # by the jazzoo file. It should print the path of the file of the definition.
    if env.step(
        env.run_jaz("--which", "fe.lint"),
    ):
        assert env.exit_code == 0
        assert env.output_lines() == [env.path("shop/fe/lint.jaz")]

    # We run jaz --which fb.
    #
    # There is no target fb, so the alias should be expanded, and it should print
    # the path of the file of fe.build.
    if env.step(
        env.run_jaz("--which", "fb"),
    ):
        assert env.exit_code == 0
        assert env.output_lines() == [env.path("shop/fe/fe.jaz")]

    # We run jaz --which nope.
    #
    # It should raise a JazzooError, as when the target runs.
    if env.step(
        env.run_jaz_and_catch_error("--which", "nope"),
    ):
        assert isinstance(env.error, JazzooError)
        assert "no such target: nope" in str(env.error)
        assert env.output == ""

    # We run jaz --which fe.nope.
    #
    # The layer exists, but the target does not.
    if env.step(
        env.run_jaz_and_catch_error("--which", "fe.nope"),
    ):
        assert isinstance(env.error, JazzooError)
        assert "no such target: fe.nope" in str(env.error)

    # We run jaz --which nope through the console script.
    #
    # It should print the error, and exit with 1.
    if env.step(
        env.run_jaz_cli("--which", "nope"),
    ):
        assert env.exit_code == 1
        assert env.output == ""
        assert "no such target: nope" in env.printed_err

    # We go to the parent directory, and run jaz --file shop/jazzoo --which build.
    #
    # The path should still be absolute.
    if env.step(
        env.change_dir(),
        env.run_jaz("--file", "shop/jazzoo", "--which", "build"),
    ):
        assert env.exit_code == 0
        assert env.output_lines() == [env.path("shop/jazzoo")]


class Env(TestEnv):
    pass
