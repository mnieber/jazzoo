from zoo_tests.zoo_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_list(context: Context):
    # Create the test environment
    env = create_env(context)

    # We list the envs of an empty registry.
    #
    # Nothing should be printed.
    if env.step(
        env.run_zoo("env", "--list"),
    ):
        assert env.output == ""

    # We register the projects blog (with its venv outside the project), groupy
    # and shop, and list the envs while shop is active.
    #
    # shop should be marked with a "*", and the root directories should be
    # aligned after the longest name.
    if env.step(
        env.write_project("blog"),
        env.make_fake_venv("venvs/blog"),
        env.init_env("blog", venv="venvs/blog"),
        env.add_project("groupy"),
        env.init_env("groupy"),
        env.add_project("shop"),
        env.init_env("shop"),
        env.set_env("JAZZOO_ENV", "shop"),
        env.run_zoo("env", "--list"),
    ):
        assert env.output.splitlines() == [
            "  blog    " + env.path("projects/blog"),
            "  groupy  " + env.path("projects/groupy"),
            "* shop    " + env.path("projects/shop"),
        ]

    # We remove the venv of groupy and the project directory of blog, and list
    # the envs.
    #
    # The envs are still registered, and should be listed with what is missing.
    if env.step(
        env.remove_dir("projects/groupy/.venv"),
        env.remove_dir("projects/blog"),
        env.run_zoo("env", "--list"),
    ):
        assert env.output.splitlines() == [
            "  blog    " + env.path("projects/blog") + " (root dir missing)",
            "  groupy  " + env.path("projects/groupy") + " (venv missing)",
            "* shop    " + env.path("projects/shop"),
        ]


class Env(TestEnv):
    pass
