from zoo_tests.zoo_test_env import FISH_FILES, Context, TestEnv

# Each of these breaks a rule of how --names and --install-fish combine with the
# other options of `zoo env`
USAGE_ERRORS = [
    ["env", "--names"],
    ["env", "shop", "--names"],
    ["env", "--install-fish", "shop"],
    ["env", "--install-fish", "-"],
    ["env", "--install-fish", "--latest"],
    ["env", "--install-fish", "--init", "shop", "--use-venv", ".venv"],
    ["env", "--install-fish", "--forget", "shop"],
    ["env", "--install-fish", "--list"],
]


def create_env(context: Context):
    return Env(context)


def test_install_fish_usage_errors(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a project shop with a venv, and change to its directory.
    if env.step(
        env.add_project("shop"),
        env.change_dir("projects/shop"),
    ):
        pass

    # We run zoo env with options that do not go together.
    #
    # Each should be a usage error: zoo should exit with 2, and register and
    # install nothing.
    for args in USAGE_ERRORS:
        if env.step(
            env.run_zoo_and_catch_exit(*args),
        ):
            assert env.system_exit is not None, args
            assert env.system_exit.code == 2, args
            assert not env.exists(env.env_dir("shop")), args
            for name in FISH_FILES:
                assert not env.exists(env.fish_file(name)), args


class Env(TestEnv):
    pass
