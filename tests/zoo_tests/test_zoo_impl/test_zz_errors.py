from zoo_tests.zoo_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_zz_errors(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the registered projects shop and blog, and install the fish files.
    if env.step(
        env.add_project("shop", runnable_zoo=True),
        env.init_env("shop"),
        env.add_project("blog", runnable_zoo=True),
        env.init_env("blog"),
        env.run_zoo("env", "--install-fish"),
    ):
        pass

    # With shop active, we run `zz nosuch`.
    #
    # zoo fails, so zz should source nothing, show the error of zoo, and fail:
    # shop stays active.
    if env.step(
        env.run_fish(
            """
            zz shop
            zz nosuch
            echo status=$status
            echo $JAZZOO_ENV
            """
        ),
    ):
        assert env.fish_lines()[0] != "status=0"
        assert env.fish_lines()[1] == "shop"
        assert "no such zoo environment: nosuch" in env.completed.stderr

    # With shop active, we run `zz --list`.
    #
    # It should list the envs, as zz without arguments does, and source nothing.
    if env.step(
        env.run_fish(
            """
            zz shop
            zz --list
            echo $JAZZOO_ENV
            """
        ),
    ):
        assert env.fish_lines() == [
            "  blog  " + env.path("projects/blog"),
            "* shop  " + env.path("projects/shop"),
            "shop",
        ]

    # With shop active, we run `zz --forget blog`.
    #
    # blog should be forgotten. --forget activates nothing, so zz should source
    # nothing, and shop stays active.
    if env.step(
        env.run_fish(
            """
            zz shop
            zz --forget blog
            echo status=$status
            echo $JAZZOO_ENV
            """
        ),
    ):
        assert env.fish_lines() == ["status=0", "shop"]
        assert not env.exists(env.env_dir("blog"))


class Env(TestEnv):
    pass
