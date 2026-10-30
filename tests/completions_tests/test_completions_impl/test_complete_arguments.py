from completions_tests.completions_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_complete_arguments(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the project shop and its aliases.
    if env.step(
        env.write_jazzoo(),
        env.write_aliases(),
    ):
        pass

    # We complete the arguments of the alias fb, whose expansion is
    # `fe.build mode=debug`.
    #
    # It should offer the parameters of fe.build.
    if env.step(
        env.complete_jaz("fb", ""),
    ):
        assert env.candidates() == ["mode="]

    # We give the first argument of build positionally, and complete the next
    # argument.
    #
    # The positional argument is mode, so only watch should be offered.
    if env.step(
        env.complete_jaz("build", "release", ""),
    ):
        assert env.candidates() == ["watch="]

    # We complete a parameter of build by its first letters.
    #
    # Only the parameter that starts with them should be offered.
    if env.step(
        env.complete_jaz("build", "w"),
    ):
        assert env.candidates() == ["watch="]

    # We complete the arguments of deploy, which has no parameters.
    #
    # It should offer nothing.
    if env.step(
        env.complete_jaz("deploy", ""),
    ):
        assert env.exit_code == 0
        assert env.output == ""

    # We look at the descriptions of the parameters.
    #
    # Parameters should have no description.
    if env.step(
        env.complete_jaz("build", ""),
    ):
        assert env.descriptions() == {"mode=": None, "watch=": None}


class Env(TestEnv):
    pass
