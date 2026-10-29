from zoo_tests.zoo_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_run_a_target_from_anywhere(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the registered projects shop and blog. Their target `where` prints
    # the current directory and ⚙️.invocation_dir.
    if env.step(
        env.add_project("shop"),
        env.init_env("shop"),
        env.add_project("blog"),
        env.init_env("blog"),
    ):
        pass

    # In some other directory, we run `zoo where` with the zoo of the venv of
    # shop.
    #
    # The target should run in the project directory of shop, while
    # ⚙️.invocation_dir is the directory that we called zoo from.
    if env.step(
        env.make_dir("elsewhere"),
        env.change_dir("elsewhere"),
        env.use_zoo_of("projects/shop/.venv"),
        env.run_zoo("where"),
    ):
        assert env.exit_code == 0
        assert env.output.splitlines() == [
            "cwd=" + env.path("projects/shop"),
            "invocation_dir=" + env.path("elsewhere"),
        ]

    # We run zoo without arguments.
    #
    # As jaz does, it should list the targets of shop.
    if env.step(
        env.change_dir("elsewhere"),
        env.run_zoo(),
    ):
        assert env.output.splitlines() == ["where", "greet"]

    # We run `zoo where` with the zoo of the venv of blog.
    #
    # This zoo belongs to blog, so the target of blog should run.
    if env.step(
        env.change_dir("elsewhere"),
        env.use_zoo_of("projects/blog/.venv"),
        env.run_zoo("where"),
    ):
        assert env.output.splitlines()[0] == "cwd=" + env.path("projects/blog")


class Env(TestEnv):
    pass
