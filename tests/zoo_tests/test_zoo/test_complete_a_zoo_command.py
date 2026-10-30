from zoo_tests.zoo_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_complete_a_zoo_command(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the registered projects shop and blog, use the zoo of shop, and are
    # in a directory outside the projects.
    if env.step(
        env.add_project("shop"),
        env.init_env("shop"),
        env.add_project("blog"),
        env.init_env("blog"),
        env.use_zoo_of("projects/shop/.venv"),
        env.make_dir("elsewhere"),
        env.change_dir("elsewhere"),
    ):
        pass

    # We type `zoo ` and press tab.
    #
    # It should offer env, and the targets of the jazzoo file of shop, which zoo
    # reads from the root directory of shop.
    if env.step(
        env.complete_zoo(""),
    ):
        assert env.exit_code == 0
        assert sorted(env.candidates()) == ["env", "greet", "where"]

    # We choose greet, and press tab for its arguments.
    #
    # It should offer the parameter of greet.
    if env.step(
        env.complete_zoo("greet", ""),
    ):
        assert env.candidates() == ["name="]

    # We type `zoo env ` and press tab.
    #
    # It should offer the names of the registered envs, `-` for the previous env,
    # and the options of zoo env.
    if env.step(
        env.complete_zoo("env", ""),
    ):
        assert {"blog", "shop", "-", "--list", "--forget"} <= set(env.candidates())

    # We type `zoo env --forget ` and press tab.
    #
    # Only a name can be forgotten, so it should only offer the names.
    if env.step(
        env.complete_zoo("env", "--forget", ""),
    ):
        assert sorted(env.candidates()) == ["blog", "shop"]


class Env(TestEnv):
    pass
