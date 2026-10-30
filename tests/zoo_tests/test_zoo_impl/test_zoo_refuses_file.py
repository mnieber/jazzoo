from zoo_tests.zoo_test_env import SHOP_JAZZOO, Context, TestEnv

from jazzoo.zoo.errors import ZooUsageError

OTHER_JAZ = """
hello():
    @echo "hello from other.jaz"
"""

# Each of these gives zoo a --file
FILE_ARGS = [
    ["--file", "other.jaz", "hello"],
    ["--file=other.jaz", "hello"],
    ["hello", "--file", "other.jaz"],
]


def create_env(context: Context):
    return Env(context)


def test_zoo_refuses_file(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the registered project shop with a second jazzoo file other.jaz,
    # and use its zoo in another directory.
    if env.step(
        env.add_project("shop", SHOP_JAZZOO),
        env.write_file("projects/shop/other.jaz", OTHER_JAZ),
        env.init_env("shop"),
        env.use_zoo_of("projects/shop/.venv"),
        env.make_dir("elsewhere"),
        env.change_dir("elsewhere"),
    ):
        pass

    # We give zoo a --file, in each of its forms.
    #
    # Each should raise a ZooUsageError, and run nothing.
    for args in FILE_ARGS:
        if env.step(
            env.run_zoo_and_catch_error(*args),
        ):
            assert isinstance(env.error, ZooUsageError), args
            assert env.output == ""

    # We run `zoo --file other.jaz hello` as the console script.
    #
    # It should tell us to import the file as a layer, and exit with 1.
    if env.step(
        env.run_zoo_cli("--file", "other.jaz", "hello"),
    ):
        assert env.exit_code == 1
        assert env.printed_err == (
            "zoo: error: --file is not valid with zoo; "
            "import the file as a layer instead\n"
        )

    # We run `zoo -- --file`.
    #
    # zoo should not refuse a --file after `--`, but pass it on to jaz, which
    # gives its own usage error.
    if env.step(
        env.run_zoo_and_catch_exit("--", "--file"),
    ):
        assert env.system_exit is not None
        assert env.system_exit.code == 2


class Env(TestEnv):
    pass
