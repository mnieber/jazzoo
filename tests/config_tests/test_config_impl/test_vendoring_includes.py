import os
import shutil
import subprocess
import sys
import typing as T
from pathlib import Path

from config_tests.config_test_env import Context, TestEnv

import jazzoo.config

# Blocks jazzoo and an installed PyYAML, so that the copy can only work on its own
VENDORED_SCRIPT = """
import sys

sys.modules["jazzoo"] = None
sys.modules["yaml"] = None
sys.path.insert(0, sys.argv[1])

from myproject.jazzoo_config import get_config

print(get_config("/docker/shell"))
"""


def create_env(context: Context):
    return Env(context)


def test_vendoring_includes(context: Context):
    # Create the test environment
    env = create_env(context)

    # We copy jazzoo.config into a project as myproject.jazzoo_config. The config
    # file includes a docker layer. A script that cannot import jazzoo or yaml reads
    # a value of the layer through the copy.
    #
    # The script should print the value of the layer.
    if env.step(
        env.copy_config_package("myproject/jazzoo_config"),
        env.write_file("myproject/__init__.py", ""),
        env.write_config("config.yaml", "jazzoo:\n  includes: [docker.yaml]\n"),
        env.write_config("docker.yaml", "docker:\n  shell: sh\n"),
        env.use_config_files("config.yaml"),
        env.run_python(VENDORED_SCRIPT, env.path("")),
    ):
        assert env.exit_code == 0, env.error_output
        assert env.output == "sh\n"


class Env(TestEnv):
    def __post_init__(self):
        super().__post_init__()
        self.exit_code: T.Optional[int] = None
        self.error_output: T.Optional[str] = None

    def copy_config_package(self, name: str):
        shutil.copytree(
            Path(jazzoo.config.__file__).parent,
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
