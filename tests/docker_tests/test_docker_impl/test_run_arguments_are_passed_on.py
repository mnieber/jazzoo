from docker_tests.docker_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_run_arguments_are_passed_on(context: Context):
    # Create the test environment
    env = create_env(context)

    # We decorate the recording function, and call it with capture, check and echo
    # set to the opposite of their defaults.
    #
    # The function should have received them unchanged, and its result should have
    # been returned as is.
    if env.step(
        env.decorate_recorder("blogs_be"),
        env.call_decorated(["ls"], capture=True, check=False, echo=True),
    ):
        assert env.recorded_calls[-1]["capture"] is True
        assert env.recorded_calls[-1]["check"] is False
        assert env.recorded_calls[-1]["echo"] is True
        assert env.result is env.recorder_results[-1]

    # We call it without these arguments.
    #
    # The function should have received the defaults of run.
    if env.step(
        env.call_decorated(["ls"]),
    ):
        assert env.recorded_calls[-1]["capture"] is False
        assert env.recorded_calls[-1]["check"] is True
        assert env.recorded_calls[-1]["echo"] is False


class Env(TestEnv):
    pass
