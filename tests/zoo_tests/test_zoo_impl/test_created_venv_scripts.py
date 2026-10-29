import os

from zoo_tests.zoo_test_env import SHOP_JAZZOO, Context, TestEnv

# A target with a Python block that imports jazzoo, and shows which python runs it
JAZZOO = SHOP_JAZZOO + """
check():
    #!/usr/bin/env python3
    import sys
    from jazzoo import run
    print("prefix=" + sys.prefix)
"""


def create_env(context: Context):
    return Env(context)


def test_created_venv_scripts(context: Context):
    # Create the test environment
    env = create_env(context)

    # We register the project shop with a new venv, without pip.
    if env.step(
        env.write_project("shop", JAZZOO),
        env.change_dir("projects/shop"),
        env.run_zoo("env", "--init", "--create-venv", "--without-pip"),
    ):
        pass

    # We look at the bin directory of the venv.
    #
    # It was created without pip.
    if env.step():
        assert not env.exists(env.path("projects/shop/.venv/bin/pip"))

    # In the project directory, we run `.venv/bin/jaz greet`.
    #
    # jaz should run the target of the jazzoo file in the current directory.
    if env.step(
        env.run_program(
            env.path("projects/shop/.venv/bin/jaz"), "greet", cwd="projects/shop"
        ),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout == "hello you\n"

    # We run `.venv/bin/jaz-run -c "echo hi"`.
    if env.step(
        env.run_program(
            env.path("projects/shop/.venv/bin/jaz-run"),
            "-c",
            "echo hi",
            cwd="projects/shop",
        ),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout == "hi\n"

    # With the bin directory of the venv first on the PATH, as after activating
    # it, we run a target whose Python block imports jazzoo.
    #
    # The block should run with the python of the venv, which can import jazzoo.
    if env.step(
        env.put_venv_on_path("projects/shop/.venv"),
        env.run_program(env.path("projects/shop/.venv/bin/zoo"), "check", cwd=""),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout.splitlines()[-1] == "prefix=" + env.path(
            "projects/shop/.venv"
        )


class Env(TestEnv):
    def put_venv_on_path(self, venv: str):
        self.set_env("PATH", self.path(f"{venv}/bin") + os.pathsep + os.environ["PATH"])
