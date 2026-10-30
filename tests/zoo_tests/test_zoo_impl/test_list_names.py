from zoo_tests.zoo_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_list_names(context: Context):
    # Create the test environment
    env = create_env(context)

    # We list the names of the envs of an empty registry.
    #
    # Nothing should be printed.
    if env.step(
        env.run_zoo("env", "--list", "--names"),
    ):
        assert env.output == ""

    # We register blog, groupy and shop, and list the names while shop is active.
    #
    # The names should be printed one per line, without the marker of the
    # active env and without the root directories.
    if env.step(
        env.add_project("blog"),
        env.init_env("blog"),
        env.add_project("groupy"),
        env.init_env("groupy"),
        env.add_project("shop"),
        env.init_env("shop"),
        env.set_env("JAZZOO_ENV", "shop"),
        env.run_zoo("env", "--list", "--names"),
    ):
        assert env.output.splitlines() == ["blog", "groupy", "shop"]

    # We remove the project directory of blog, and list the names again.
    #
    # blog is still registered, so it should still be listed, without saying
    # what is missing.
    if env.step(
        env.remove_dir("projects/blog"),
        env.run_zoo("env", "--list", "--names"),
    ):
        assert env.output.splitlines() == ["blog", "groupy", "shop"]


class Env(TestEnv):
    pass
