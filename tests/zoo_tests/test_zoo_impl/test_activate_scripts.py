from zoo_tests.zoo_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_activate_scripts(context: Context):
    # Create the test environment
    env = create_env(context)

    # We register the project shop.
    if env.step(
        env.add_project("shop"),
        env.init_env("shop"),
    ):
        pass

    # We look at activate.bash of shop.
    #
    # It should set JAZZOO_ENV, deactivate the active venv (only if there is
    # one), and then source the activate script of the venv. The venv is found
    # through the link in the registry, so that relinking venv_dir is enough to
    # move the venv.
    if env.step():
        assert env.read_lines(env.env_dir("shop") + "/activate.bash") == [
            "export JAZZOO_ENV=shop",
            'if [ -n "$VIRTUAL_ENV" ]; then',
            "deactivate",
            "fi",
            f"source {env.env_dir('shop')}/venv_dir/bin/activate",
        ]

    # We look at activate.fish of shop.
    #
    # It should do the same in fish, with the fish activate script of the venv.
    if env.step():
        assert env.read_lines(env.env_dir("shop") + "/activate.fish") == [
            "set -gx JAZZOO_ENV shop",
            'if test -n "$VIRTUAL_ENV"',
            "deactivate",
            "end",
            f"source {env.env_dir('shop')}/venv_dir/bin/activate.fish",
        ]


class Env(TestEnv):
    pass
