from zoo_tests.zoo_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_shell_choice(context: Context):
    # Create the test environment
    env = create_env(context)

    # We use fish, and register the project shop.
    #
    # --init should print the line that sources the fish activate script.
    if env.step(
        env.set_env("SHELL", "/usr/bin/fish"),
        env.add_project("shop"),
        env.init_env("shop"),
    ):
        assert env.output == env.source_line("shop", shell="fish")

    # We activate shop in fish.
    if env.step(
        env.run_zoo("env", "shop"),
    ):
        assert env.output == env.source_line("shop", shell="fish")

    # We activate shop in zsh and in bash.
    #
    # Every shell other than fish should get the bash activate script.
    for shell in ["/bin/zsh", "/bin/bash"]:
        if env.step(
            env.set_env("SHELL", shell),
            env.run_zoo("env", "shop"),
        ):
            assert env.output == env.source_line("shop", shell="bash"), shell

    # We activate shop without SHELL.
    if env.step(
        env.unset_env("SHELL"),
        env.run_zoo("env", "shop"),
    ):
        assert env.output == env.source_line("shop", shell="bash")


class Env(TestEnv):
    pass
