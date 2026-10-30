from zoo_tests.zoo_test_env import Context, TestEnv

NO_ZOO = "zz: no zoo found; register a project with zoo env --init"


def create_env(context: Context):
    return Env(context)


def test_zz_finds_zoo(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the registered project shop, and install the fish files.
    if env.step(
        env.add_project("shop", runnable_zoo=True),
        env.init_env("shop"),
        env.run_zoo("env", "--install-fish"),
    ):
        pass

    # In a fish where no env is active, and zoo is not on the PATH, we run
    # `zz shop`.
    #
    # zz should run the zoo of shop through the link zoo-shop in ~/.local/bin,
    # and activate shop.
    if env.step(
        env.run_fish(
            """
            type -q zoo; or echo no-zoo
            zz shop
            echo $JAZZOO_ENV
            """
        ),
    ):
        assert env.fish_lines() == ["no-zoo", "shop"]

    # We forget shop, which removes the link zoo-shop, and run `zz shop` again.
    #
    # There is no zoo to run, so zz should say how to get one, and fail.
    if env.step(
        env.run_zoo("env", "--forget", "shop"),
        env.run_fish(
            """
            zz shop
            echo status=$status
            """
        ),
    ):
        assert not env.exists(env.zoo_link("shop"))
        assert NO_ZOO in env.completed.stderr
        assert env.fish_lines() != ["status=0"]


class Env(TestEnv):
    pass
