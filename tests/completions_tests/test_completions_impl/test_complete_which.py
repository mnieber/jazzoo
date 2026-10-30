from completions_tests.completions_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_complete_which(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the project shop, without aliases.
    if env.step(
        env.write_jazzoo(),
    ):
        pass

    # We complete `jaz --wh`.
    #
    # It should offer the option --which.
    if env.step(
        env.complete_jaz("--wh"),
    ):
        assert env.candidates() == ["--which"]

    # We complete `jaz --which f`.
    #
    # The word after --which is a target, so it should offer the layer fe.
    if env.step(
        env.complete_jaz("--which", "f"),
    ):
        assert env.candidates() == ["fe."]


class Env(TestEnv):
    pass
