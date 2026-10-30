from completions_tests.completions_test_env import SHOP_JAZZOO, Context, TestEnv

# A top-level assignment that runs a block, which writes the file marker
JAZZOO = (
    SHOP_JAZZOO
    + """
[private]
_mark():
    touch marker

🐆.marked = 🐭._mark()
"""
)


def create_env(context: Context):
    return Env(context)


def test_complete_without_running(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the project shop, whose jazzoo file runs a block when it is loaded.
    if env.step(
        env.write_jazzoo(JAZZOO),
    ):
        pass

    # We complete `jaz `.
    #
    # It should offer the targets, without running the top-level statements of
    # the jazzoo file: the marker should not exist.
    if env.step(
        env.complete_jaz(""),
    ):
        assert "build" in env.candidates()
        assert not env.file_exists("shop/marker")

    # We run `jaz --list`.
    #
    # --list loads the jazzoo file as before, so it should run the statements and
    # write the marker.
    if env.step(
        env.run_jaz("--list"),
    ):
        assert env.exit_code == 0
        assert env.file_exists("shop/marker")


class Env(TestEnv):
    pass
