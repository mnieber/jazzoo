from zoo_tests.zoo_test_env import Context, TestEnv

# Each of these breaks a rule of how the options of `zoo env` combine
USAGE_ERRORS = [
    ["env", "--init", "shop"],
    ["env", "--venv-path", ".venv"],
    ["env", "--create-venv"],
    ["env", "--init", "shop", "--venv-path", ".venv", "--without-pip"],
    ["env", "--init", "shop", "--create-venv", "--use-venv", ".venv"],
    ["env", "--init", "shop", "--forget", "shop"],
    ["env", "--list", "shop"],
    ["env", "shop", "--latest"],
    ["env", "-", "--latest"],
]


def create_env(context: Context):
    return Env(context)


def test_usage_errors(context: Context):
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
    # Each should be a usage error: zoo should exit with 2, and register nothing.
    for args in USAGE_ERRORS:
        if env.step(
            env.run_zoo_and_catch_exit(*args),
        ):
            assert env.system_exit is not None, args
            assert env.system_exit.code == 2, args
            assert not env.exists(env.env_dir("shop")), args


class Env(TestEnv):
    pass
