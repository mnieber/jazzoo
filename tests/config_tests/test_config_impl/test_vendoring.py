import os
import re
import shutil
import subprocess
import sys
import typing as T
from pathlib import Path

from config_tests.config_test_env import Context, TestEnv

import jazzoo
import jazzoo.config

# Blocks jazzoo and an installed PyYAML, so that the copy can only work on its own
VENDORED_SCRIPT = """
import sys

sys.modules["jazzoo"] = None
sys.modules["yaml"] = None
sys.path.insert(0, sys.argv[1])

from myproject.jazzoo_config import get_config

print(get_config("/root/src"))
"""


def create_env(context: Context):
    return Env(context)


def test_vendoring(context: Context):
    # Create the test environment
    env = create_env(context)

    # We look at the modules of jazzoo.config.
    #
    # None of them should import jazzoo with an absolute import, so that the
    # sub-package keeps working when it is copied under another name.
    if env.step():
        assert env.config_modules_matching(r"^\s*(from|import)\s+jazzoo\b") == []

    # We look at the vendored PyYAML.
    #
    # It should have its license, and no cyaml.py. No module in it should import
    # yaml with an absolute import, because that could pick up an installed PyYAML.
    if env.step():
        assert (env.vendored_yaml_dir() / "LICENSE").exists()
        assert not (env.vendored_yaml_dir() / "cyaml.py").exists()
        assert env.config_modules_matching(r"^\s*(from|import)\s+yaml\b") == []

    # We copy jazzoo.config into a project as myproject.jazzoo_config, and run a
    # script that cannot import jazzoo or yaml, and reads the config through the
    # copy.
    #
    # The script should print the source dir.
    if env.step(
        env.copy_config_package("myproject/jazzoo_config"),
        env.write_file("myproject/__init__.py", ""),
        env.write_config("config.yaml", "root:\n  src: /home/jane/shop/src\n"),
        env.use_config_files("config.yaml"),
        env.run_python(VENDORED_SCRIPT, env.path("")),
    ):
        assert env.exit_code == 0, env.error_output
        assert env.output == "/home/jane/shop/src\n"

    # We look at the jazzoo facade.
    #
    # It should re-export get_config, prepare_config and the config errors.
    if env.step():
        for name in [
            "get_config",
            "prepare_config",
            "ConfigError",
            "ConfigFileError",
            "ConfigKeyError",
            "ConfigExpansionError",
        ]:
            assert name in jazzoo.__all__
            assert getattr(jazzoo, name) is getattr(jazzoo.config, name)


class Env(TestEnv):
    def __post_init__(self):
        super().__post_init__()
        self.exit_code: T.Optional[int] = None
        self.error_output: T.Optional[str] = None

    def copy_config_package(self, name: str):
        shutil.copytree(
            self.config_package_dir(),
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

    def config_package_dir(self) -> Path:
        return Path(jazzoo.config.__file__).parent

    def vendored_yaml_dir(self) -> Path:
        return self.config_package_dir() / "_vendor" / "yaml"

    def config_modules_matching(self, pattern: str) -> T.List[str]:
        root = self.config_package_dir()
        return [
            str(path.relative_to(root))
            for path in root.rglob("*.py")
            if re.search(pattern, path.read_text(encoding="utf-8"), re.M)
        ]
