from zoo_tests.zoo_test_env import FISH_FILES, Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_install_fish_locations(context: Context):
    # Create the test environment
    env = create_env(context)

    # We set XDG_CONFIG_HOME, and run the installer.
    #
    # Like fish itself, it should use $XDG_CONFIG_HOME/fish, and the startup
    # file should source latest.fish of the registry in $XDG_CONFIG_HOME/jazzoo.
    if env.step(
        env.set_env("XDG_CONFIG_HOME", env.path("xdg")),
        env.run_zoo("env", "--install-fish"),
    ):
        for name in FISH_FILES:
            assert env.exists(env.path(f"xdg/fish/{name}")), name
            assert not env.exists(env.fish_file(name)), name
        assert env.path("xdg/jazzoo/latest.fish") in env.read_file(
            env.path("xdg/fish/conf.d/zoo.fish")
        )

    # We set XDG_CONFIG_HOME to the empty string, and run the installer.
    #
    # An empty XDG_CONFIG_HOME counts as unset, so it should use ~/.config/fish.
    if env.step(
        env.set_env("XDG_CONFIG_HOME", ""),
        env.run_zoo("env", "--install-fish"),
    ):
        for name in FISH_FILES:
            assert env.exists(env.fish_file(name)), name
        assert env.config_dir() + "/latest.fish" in env.read_file(
            env.fish_file("conf.d/zoo.fish")
        )


class Env(TestEnv):
    pass
