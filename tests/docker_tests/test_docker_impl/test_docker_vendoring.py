import os
import shutil
import subprocess
import sys
import typing as T
from pathlib import Path

from docker_tests.docker_test_env import Context, TestEnv

import jazzoo
import jazzoo.commands

# Blocks jazzoo, so that the copy can only work on its own. It replaces run with
# the decorated one.
VENDORED_SCRIPT = """
import sys

sys.modules["jazzoo"] = None
sys.path.insert(0, sys.argv[1])

from myproject.jazzoo_commands import run, run_docker

run = run_docker("blogs_be")(run)

print(run("echo vendored", capture=True).stdout, end="")
"""


def create_env(context: Context):
    return Env(context)


def test_docker_vendoring(context: Context):
    # Create the test environment
    env = create_env(context)

    # We copy jazzoo.commands into a project as myproject.jazzoo_commands, and run
    # a script that cannot import jazzoo, and that replaces run with the version
    # that runs in the container blogs_be. It runs a command.
    #
    # The command should have run with docker exec, and the script should print its
    # output.
    if env.step(
        env.install_fake_docker(),
        env.copy_commands_package("myproject/jazzoo_commands"),
        env.write_file("myproject/__init__.py", ""),
        env.run_python(VENDORED_SCRIPT, env.path("")),
    ):
        assert env.exit_code == 0, env.error_output
        assert env.output == "vendored\n"
        assert env.docker_calls() == [
            ["exec", "--interactive", "blogs_be", "bash", "-c", "echo vendored"]
        ]

    # We look at the facades.
    #
    # jazzoo.commands should export run_docker, and jazzoo should re-export it.
    if env.step():
        assert "run_docker" in jazzoo.commands.__all__
        assert "run_docker" in jazzoo.__all__
        assert jazzoo.run_docker is jazzoo.commands.run_docker


class Env(TestEnv):
    def __post_init__(self):
        super().__post_init__()
        self.exit_code: T.Optional[int] = None
        self.error_output: T.Optional[str] = None

    def copy_commands_package(self, name: str):
        shutil.copytree(
            Path(jazzoo.commands.__file__).parent,
            self.path(name),
            ignore=shutil.ignore_patterns("__pycache__"),
        )

    def run_python(self, script: str, *args: str):
        result = subprocess.run(
            [sys.executable, "-c", script, *args],
            env=dict(os.environ),
            capture_output=True,
            text=True,
        )
        self.exit_code = result.returncode
        self.output = result.stdout
        self.error_output = result.stderr
