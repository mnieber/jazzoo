from zoo_tests.zoo_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_find_the_current_env(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the registered projects blog and shop, and no env is active.
    if env.step(
        env.add_project("blog"),
        env.init_env("blog"),
        env.add_project("shop"),
        env.init_env("shop"),
    ):
        pass

    # We run zoo --which.
    #
    # No env is active, so it should print nothing, and succeed.
    if env.step(
        env.run_zoo("--which"),
    ):
        assert env.exit_code == 0
        assert env.output == ""

    # We activate shop, and run zoo --which.
    #
    # It should print the name and the root directory of shop, as in
    # zoo env --list.
    if env.step(
        env.set_env("JAZZOO_ENV", "shop"),
        env.run_zoo("--which"),
    ):
        assert env.exit_code == 0
        assert env.output.splitlines() == ["shop  " + env.path("projects/shop")]

    # We run zoo --which greet with the zoo of the venv of shop.
    #
    # It should print the file that defines greet: the jazzoo file of shop.
    if env.step(
        env.use_zoo_of("projects/shop/.venv"),
        env.run_zoo("--which", "greet"),
    ):
        assert env.exit_code == 0
        assert env.output.splitlines() == [env.path("projects/shop/jazzoo")]


class Env(TestEnv):
    pass
