import importlib.metadata
import os
import subprocess
import sys
from pathlib import Path

from zoo_tests.zoo_test_env import Context, TestEnv

SRC_DIR = "checkout/src"
VENV = "projects/shop/.venv"

# Shows which version the venv sees, and where it imports jazzoo from
SHOW_JAZZOO = """
import importlib.metadata, jazzoo
print(importlib.metadata.version("jazzoo"))
print(jazzoo.__file__)
"""

IMPORT_OTHER = "import other"


def create_env(context: Context):
    return Env(context)


def test_linked_source_tree(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a source tree with a copy of the jazzoo package, which has no
    # package metadata, next to the package other. With the source tree on
    # PYTHONPATH, we ask python which version of jazzoo it sees, and where it
    # imports jazzoo from.
    #
    # Python should import the copy, but still see the package metadata of the
    # jazzoo that runs the tests, which is installed in another directory.
    if env.step(
        env.copy_jazzoo_package(SRC_DIR),
        env.write_file(f"{SRC_DIR}/other/__init__.py", 'NAME = "other"\n'),
        env.run_python_with_source_tree(SRC_DIR, SHOW_JAZZOO),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout.splitlines() == [
            importlib.metadata.version("jazzoo"),
            env.path(f"{SRC_DIR}/jazzoo/__init__.py"),
        ]

    # We have the project shop. In its directory, we run the zoo of the source
    # tree: `zoo env --init --create-venv --without-pip`.
    #
    # The metadata that python sees does not describe the copy, so the version
    # should be 0.0.0.
    if env.step(
        env.write_project("shop"),
        env.run_zoo_from_copy(
            SRC_DIR,
            "env",
            "--init",
            "--create-venv",
            "--without-pip",
            cwd="projects/shop",
        ),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.dist_info_names(VENV) == ["jazzoo-0.0.0.dist-info"]

    # We ask the python of the venv which version of jazzoo it sees, and where it
    # imports jazzoo from.
    #
    # It should see 0.0.0, and import the jazzoo of the source tree, to which
    # direct_url.json points too.
    if env.step(
        env.run_python_in_venv(VENV, SHOW_JAZZOO),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout.splitlines() == [
            "0.0.0",
            env.path(f"{SRC_DIR}/jazzoo/__init__.py"),
        ]
        assert env.read_direct_url(VENV)["url"] == (
            Path(env.path(f"{SRC_DIR}/jazzoo")).as_uri()
        )

    # In the venv, we import the package other.
    #
    # The finder only answers for jazzoo, so other, which is next to the linked
    # package, should not be found.
    if env.step(
        env.run_python_in_venv(VENV, IMPORT_OTHER),
    ):
        assert env.completed.returncode != 0
        assert "ModuleNotFoundError: No module named 'other'" in env.completed.stderr


class Env(TestEnv):
    def run_python_with_source_tree(self, src_dir: str, code: str):
        """Runs code with the python of the test run, and <src_dir> on PYTHONPATH."""
        self.completed = subprocess.run(
            [sys.executable, "-c", code],
            cwd=self.path(""),
            env=dict(os.environ, PYTHONPATH=self.path(src_dir)),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=60,
        )
