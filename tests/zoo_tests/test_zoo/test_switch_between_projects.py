from zoo_tests.zoo_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_switch_between_projects(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the registered projects shop and blog.
    if env.step(
        env.add_project("shop"),
        env.init_env("shop"),
        env.add_project("blog"),
        env.init_env("blog"),
    ):
        pass

    # We activate shop.
    #
    # zoo should print the line that sources the activate script of shop.
    if env.step(
        env.run_zoo("env", "shop"),
    ):
        assert env.output == env.source_line("shop")

    # We activate blog.
    if env.step(
        env.run_zoo("env", "blog"),
    ):
        assert env.output == env.source_line("blog")

    # We go back to the previous env with `zoo env -`.
    #
    # The previous env is shop.
    if env.step(
        env.run_zoo("env", "-"),
    ):
        assert env.output == env.source_line("shop")

    # We run `zoo env -` once more.
    #
    # Like `cd -`, this should go back and forth: the previous env is now blog.
    if env.step(
        env.run_zoo("env", "-"),
    ):
        assert env.output == env.source_line("blog")

    # We activate the latest env, as a new terminal would.
    #
    # That is blog, which was activated last.
    if env.step(
        env.run_zoo("env", "--latest"),
    ):
        assert env.output == env.source_line("blog")


class Env(TestEnv):
    pass
