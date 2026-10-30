from zoo_tests.zoo_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_fish_startup(context: Context):
    # Create the test environment
    env = create_env(context)

    # We register shop, which makes it the latest env, and install the fish
    # files.
    if env.step(
        env.add_project("shop", runnable_zoo=True),
        env.init_env("shop"),
        env.run_zoo("env", "--install-fish"),
    ):
        pass

    # We start an interactive fish.
    #
    # It should start in shop, the env that was activated last.
    if env.step(
        env.run_fish("echo $JAZZOO_ENV", interactive=True),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.fish_lines() == ["shop"]

    # We start a fish that is not interactive, as a fish script does.
    #
    # It should not activate an env that the script did not ask for.
    if env.step(
        env.run_fish("echo $JAZZOO_ENV"),
    ):
        assert env.fish_lines() == [""]

    # We remove the zoo registry, and start an interactive fish.
    #
    # There is no latest.fish, so the startup file should skip it, without
    # errors.
    if env.step(
        env.remove_dir("home/.config/jazzoo"),
        env.run_fish("echo $JAZZOO_ENV", interactive=True),
    ):
        assert env.completed.returncode == 0
        assert env.completed.stderr == ""
        assert env.fish_lines() == [""]


class Env(TestEnv):
    pass
