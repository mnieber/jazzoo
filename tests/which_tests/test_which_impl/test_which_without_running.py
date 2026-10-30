from which_tests.which_test_env import SHOP_JAZZOO, Context, TestEnv

# A top-level assignment that runs a block, which writes the file marker
MARKING_JAZZOO = (
    SHOP_JAZZOO
    + """
[private]
_mark():
    touch marker

🐆.marked = 🐭._mark()
"""
)

# A top-level assignment that runs a block that fails
FAILING_JAZZOO = (
    SHOP_JAZZOO
    + """
[private]
_fail():
    exit 1

🐆.failed = 🐭._fail()
"""
)


def create_env(context: Context):
    return Env(context)


def test_which_without_running(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the project shop, whose jazzoo file runs a block when it is loaded.
    if env.step(
        env.write_jazzoo(MARKING_JAZZOO),
    ):
        pass

    # We run jaz --which build.
    #
    # It should print the path, without running the top-level statements of the
    # jazzoo file: the marker should not exist.
    if env.step(
        env.run_jaz("--which", "build"),
    ):
        assert env.exit_code == 0
        assert env.output_lines() == [env.path("shop/jazzoo")]
        assert not env.file_exists("shop/marker")

    # The jazzoo file now runs a failing block when it is loaded. We run jaz
    # --which build.
    #
    # The block does not run, so it should still print the path.
    if env.step(
        env.write_jazzoo(FAILING_JAZZOO),
        env.run_jaz_cli("--which", "build"),
    ):
        assert env.exit_code == 0
        assert env.output_lines() == [env.path("shop/jazzoo")]

    # We run jaz --confirm --which build, without a terminal.
    #
    # No command runs, so it should not need a terminal.
    if env.step(
        env.run_jaz_cli("--confirm", "--which", "build"),
    ):
        assert env.exit_code == 0
        assert env.output_lines() == [env.path("shop/jazzoo")]


class Env(TestEnv):
    pass
