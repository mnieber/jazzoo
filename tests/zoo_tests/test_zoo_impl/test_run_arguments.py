from zoo_tests.zoo_test_env import SHOP_JAZZOO, Context, TestEnv

# A target named `env`, which `zoo env` would take for its own command
JAZZOO = (
    SHOP_JAZZOO
    + """
env():
    @echo "the env target"

fail():
    @exit 3
"""
)

OTHER_JAZ = """
hello():
    @echo "hello from other.jaz"
"""


def create_env(context: Context):
    return Env(context)


def test_run_arguments(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the registered project shop, and use its zoo in another
    # directory.
    if env.step(
        env.add_project("shop", JAZZOO),
        env.write_file("projects/shop/other.jaz", OTHER_JAZ),
        env.init_env("shop"),
        env.use_zoo_of("projects/shop/.venv"),
        env.make_dir("elsewhere"),
    ):
        pass

    # We pass an argument to a target, positionally and by name.
    #
    # zoo should pass the arguments on to jaz.
    if env.step(
        env.change_dir("elsewhere"),
        env.run_zoo("greet", "jane"),
    ):
        assert env.output == "hello jane\n"

    if env.step(
        env.change_dir("elsewhere"),
        env.run_zoo("greet", "name=jane"),
    ):
        assert env.output == "hello jane\n"

    # We run `zoo -- env`.
    #
    # After `--`, env is the name of a target, not the env command of zoo.
    if env.step(
        env.change_dir("elsewhere"),
        env.run_zoo("--", "env"),
    ):
        assert env.output == "the env target\n"

    # We run a target of other.jaz with `--file other.jaz`.
    #
    # The relative path should be resolved against the root directory, not
    # against the directory that we called zoo from.
    if env.step(
        env.change_dir("elsewhere"),
        env.run_zoo("--file", "other.jaz", "hello"),
    ):
        assert env.output == "hello from other.jaz\n"

    # We run a target that fails, as the console script does.
    #
    # zoo should exit with the exit code of jaz.
    if env.step(
        env.change_dir("elsewhere"),
        env.run_zoo_cli("fail"),
    ):
        assert env.exit_code == 1
        assert "error: recipe failed with exit code 3" in env.printed_err


class Env(TestEnv):
    pass
