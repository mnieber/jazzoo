from docker_tests.docker_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_empty_values(context: Context):
    # Create the test environment
    env = create_env(context)

    # We decorate the recording function, and call it with an empty string, a blank
    # string and an empty list.
    #
    # Each call should raise a ValueError, as run does, and the recording function
    # should not have been called.
    if env.step(
        env.decorate_recorder("blogs_be"),
        env.call_decorated_and_catch_error(""),
    ):
        assert isinstance(env.error, ValueError)
        assert env.recorded_calls == []

    if env.step(
        env.call_decorated_and_catch_error("   "),
    ):
        assert isinstance(env.error, ValueError)
        assert env.recorded_calls == []

    if env.step(
        env.call_decorated_and_catch_error([]),
    ):
        assert isinstance(env.error, ValueError)
        assert env.recorded_calls == []

    # We call run_docker with an empty container, and with a blank one.
    #
    # run_docker itself should raise a ValueError, before anything is decorated.
    if env.step(
        env.decorate_recorder_and_catch_error(""),
    ):
        assert isinstance(env.error, ValueError)

    if env.step(
        env.decorate_recorder_and_catch_error("  "),
    ):
        assert isinstance(env.error, ValueError)


class Env(TestEnv):
    pass
