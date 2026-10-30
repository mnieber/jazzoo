import os
import shutil
from pathlib import Path

from zoo_tests.zoo_test_env import LINKED_DIR, Context, TestEnv

VENV = "projects/shop/.venv"

SHOW_JAZZOO_FILE = "import jazzoo; print(jazzoo.__file__)"

SHOW_SUBPACKAGE_FILE = """
import jazzoo.zoo.actions.create_venv as module
print(module.__file__)
"""

SHOW_LAST_FINDER = "import sys; print(sys.meta_path[-1].__module__)"


def create_env(context: Context):
    return Env(context)


def test_linked_import_hook(context: Context):
    # Create the test environment
    env = create_env(context)

    # We register the project shop with a new venv.
    if env.step(
        env.write_project("shop"),
        env.change_dir("projects/shop"),
        env.run_zoo("env", "--init", "--create-venv", "--without-pip"),
    ):
        pass

    # In the venv, we import a subpackage of jazzoo.
    #
    # The hook only finds the package jazzoo; its subpackages should be found
    # through the package itself, in the linked directory.
    if env.step(
        env.run_python_in_venv(VENV, SHOW_SUBPACKAGE_FILE),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout.splitlines() == [
            os.path.join(LINKED_DIR, "zoo", "actions", "create_venv.py")
        ]

    # We look at the finders of the venv.
    #
    # The finder of _jazzoo_link should be the last one, after the finder of
    # sys.path.
    if env.step(
        env.run_python_in_venv(VENV, SHOW_LAST_FINDER),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout.splitlines() == ["_jazzoo_link"]

    # We write a real jazzoo package to the site-packages of the venv, and import
    # jazzoo.
    #
    # A real install wins, so the venv should import that package.
    if env.step(
        env.write_real_jazzoo_package(VENV),
        env.run_python_in_venv(VENV, SHOW_JAZZOO_FILE),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout.splitlines() == [
            os.path.join(env.site_packages(VENV), "jazzoo", "__init__.py")
        ]

    # We remove that package, and import jazzoo again.
    #
    # The venv should import the linked jazzoo again.
    if env.step(
        env.remove_real_jazzoo_package(VENV),
        env.run_python_in_venv(VENV, SHOW_JAZZOO_FILE),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout.splitlines() == [
            os.path.join(LINKED_DIR, "__init__.py")
        ]


class Env(TestEnv):
    def write_real_jazzoo_package(self, venv: str):
        path = Path(self.site_packages(venv), "jazzoo", "__init__.py")
        path.parent.mkdir()
        path.write_text('MARKER = "real"\n', encoding="utf-8")

    def remove_real_jazzoo_package(self, venv: str):
        shutil.rmtree(os.path.join(self.site_packages(venv), "jazzoo"))
