from zoo_tests.zoo_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_complete_zoo_which(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the registered project shop, and use the zoo of its venv.
    if env.step(
        env.add_project("shop"),
        env.init_env("shop"),
        env.use_zoo_of("projects/shop/.venv"),
    ):
        pass

    # We complete `zoo --wh`.
    #
    # It should offer the option --which.
    if env.step(
        env.complete_zoo("--wh"),
    ):
        assert env.candidates() == ["--which"]

    # We complete `zoo --which g`.
    #
    # The word after --which is a target, so it should offer greet.
    if env.step(
        env.complete_zoo("--which", "g"),
    ):
        assert env.candidates() == ["greet"]


class Env(TestEnv):
    pass
