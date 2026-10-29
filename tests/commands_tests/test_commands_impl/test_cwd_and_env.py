import os

from commands_tests.commands_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_cwd_and_env(context: Context):
    # Create the test environment
    env = create_env(context)

    # We are in the tmp dir, and run a command in a sub dir.
    #
    # The command should run in the sub dir, and the working directory of the
    # script should not change.
    if env.step(
        env.write_file("app/src/main.py", ""),
        env.change_dir(),
        env.run("pwd", cwd=env.path("app/src"), capture=True),
    ):
        assert os.path.realpath(env.result.stdout.strip()) == os.path.realpath(
            env.path("app/src")
        )
        assert os.path.realpath(env.cwd()) == os.path.realpath(env.path(""))

    # We run a command in a dir that does not exist, which would create a marker
    # file.
    #
    # It should raise a ValueError, and the command should not have run.
    if env.step(
        env.run_and_catch_error(
            f"touch {env.path('marker')}", cwd=env.path("no-such-dir")
        ),
    ):
        assert isinstance(env.error, ValueError)
        assert not os.path.exists(env.path("marker"))

    # We have two variables in the environment of the script, and run a command
    # with env that sets one of them and a new one.
    #
    # The command should see the variable that is only in the environment, the new
    # one from env, and the value from env for the one that is in both.
    if env.step(
        env.set_env("SHOP_ENV", "dev"),
        env.set_env("SHOP_USER", "jane"),
        env.run(
            "echo $SHOP_ENV $SHOP_USER $SHOP_PORT",
            env={"SHOP_USER": "deploy", "SHOP_PORT": "8080"},
            capture=True,
        ),
    ):
        assert env.result.stdout == "dev deploy 8080\n"

    # We look at the environment of the script.
    #
    # It should not have been changed by env.
    if env.step():
        assert env.env_var("SHOP_USER") == "jane"
        assert env.env_var("SHOP_PORT") is None


class Env(TestEnv):
    pass
