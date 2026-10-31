from zoo_tests.zoo_test_env import SHOP_JAZZOO, Context, TestEnv

# A target that starts with e, like env
JAZZOO = (
    SHOP_JAZZOO
    + """
echo-all():
    @echo "all"
"""
)


def create_env(context: Context):
    return Env(context)


def test_complete_zoo(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the registered project shop, but the zoo that we run is not in a
    # zoo env.
    if env.step(
        env.add_project("shop", JAZZOO),
        env.init_env("shop"),
        env.make_dir("elsewhere"),
        env.use_zoo_of("elsewhere"),
    ):
        pass

    # We complete `zoo `.
    #
    # Outside a zoo env there are no targets, so it should only offer env, and
    # print no error.
    if env.step(
        env.complete_zoo(""),
    ):
        assert env.exit_code == 0
        assert env.candidates() == ["env"]
        assert env.printed_err == ""

    # We use the zoo of shop, and complete `zoo e`.
    #
    # It should offer env, and the target that starts with e.
    if env.step(
        env.use_zoo_of("projects/shop/.venv"),
        env.change_dir("elsewhere"),
        env.complete_zoo("e"),
    ):
        assert sorted(env.candidates()) == ["echo-all", "env"]

    # We complete the options of zoo.
    #
    # zoo takes no --file, so it should not be offered.
    if env.step(
        env.complete_zoo("--"),
    ):
        assert "--trace" in env.candidates()
        assert "--file" not in env.candidates()

    # We complete `zoo -- `.
    #
    # After `--`, a word is a target name, so it should offer the targets, but
    # not env.
    if env.step(
        env.complete_zoo("--", ""),
    ):
        assert sorted(env.candidates()) == ["echo-all", "greet", "where"]

    # We complete `zoo env --venv-path ` and `zoo greet name=` in the directory
    # elsewhere, which has a file.
    #
    # Both should offer the file names of the current directory, not of the root
    # directory of shop.
    if env.step(
        env.write_file("elsewhere/notes.txt", ""),
        env.complete_zoo("env", "--venv-path", ""),
    ):
        assert env.candidates() == ["notes.txt"]

    if env.step(
        env.complete_zoo("greet", "name="),
    ):
        assert env.candidates() == ["name=notes.txt"]

    # We remove the root directory of shop, and complete `zoo `.
    #
    # There is no jazzoo file, so it should only offer env, and print no error.
    if env.step(
        env.remove_dir("projects/shop"),
        env.complete_zoo(""),
    ):
        assert env.exit_code == 0
        assert env.candidates() == ["env"]
        assert env.printed_err == ""


class Env(TestEnv):
    pass
