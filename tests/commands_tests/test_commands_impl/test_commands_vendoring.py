import os
import re
import shutil
import subprocess
import sys
import typing as T
from pathlib import Path

from commands_tests.commands_test_env import Context, TestEnv

import jazzoo
import jazzoo.commands

# Blocks jazzoo, so that the copy can only work on its own
VENDORED_SCRIPT = """
import sys

sys.modules["jazzoo"] = None
sys.path.insert(0, sys.argv[1])

from myproject.jazzoo_commands import run

print(run("echo vendored", capture=True).stdout, end="")
"""

# Runs the copy as `python3 -m myproject.jazzoo_commands -c "echo vendored"`, with
# jazzoo blocked
VENDORED_MAIN_SCRIPT = """
import runpy
import sys

sys.modules["jazzoo"] = None
sys.path.insert(0, sys.argv[1])
sys.argv = ["jazzoo_commands", "-c", "echo vendored"]

runpy.run_module("myproject.jazzoo_commands", run_name="__main__", alter_sys=True)
"""

FACADE_NAMES = [
    "run",
    "CommandResult",
    "CommandError",
    "CommandNotFoundError",
    "CommandFailedError",
    "CommandAbortedError",
]


def create_env(context: Context):
    return Env(context)


def test_commands_vendoring(context: Context):
    # Create the test environment
    env = create_env(context)

    # We look at the modules of jazzoo.commands.
    #
    # None of them should import jazzoo with an absolute import, so that the
    # sub-package keeps working when it is copied under another name. In
    # particular, none of them should use jazzoo.config.
    if env.step():
        assert env.commands_modules_matching(r"^\s*(from|import)\s+jazzoo\b") == []
        assert env.commands_modules_matching(r"^\s*from\s+\.\.+config\b") == []

    # We copy jazzoo.commands into a project as myproject.jazzoo_commands, and run
    # a script that cannot import jazzoo, and runs a command through the copy.
    #
    # The script should print the output of the command.
    if env.step(
        env.copy_commands_package("myproject/jazzoo_commands"),
        env.write_file("myproject/__init__.py", ""),
        env.run_python(VENDORED_SCRIPT, env.path("")),
    ):
        assert env.exit_code == 0, env.error_output
        assert env.output == "vendored\n"

    # We run the copy as a module, as jaz-run, with a string command, from a script
    # that cannot import jazzoo.
    #
    # The copy should run the command, and exit with 0.
    if env.step(
        env.run_python(VENDORED_MAIN_SCRIPT, env.path("")),
    ):
        assert env.exit_code == 0, env.error_output
        assert env.output == "vendored\n"

    # We look at the jazzoo facade.
    #
    # It should re-export run, CommandResult and the command errors.
    if env.step():
        for name in FACADE_NAMES:
            assert name in jazzoo.__all__
            assert getattr(jazzoo, name) is getattr(jazzoo.commands, name)


class Env(TestEnv):
    def __post_init__(self):
        super().__post_init__()
        self.exit_code: T.Optional[int] = None
        self.error_output: T.Optional[str] = None

    def copy_commands_package(self, name: str):
        shutil.copytree(
            self.commands_package_dir(),
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

    # Queries

    def commands_package_dir(self) -> Path:
        return Path(jazzoo.commands.__file__).parent

    def commands_modules_matching(self, pattern: str) -> T.List[str]:
        root = self.commands_package_dir()
        return [
            str(path.relative_to(root))
            for path in root.rglob("*.py")
            if re.search(pattern, path.read_text(encoding="utf-8"), re.M)
        ]
