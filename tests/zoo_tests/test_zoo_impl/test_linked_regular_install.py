import os
import shutil
import subprocess
import sys
from pathlib import Path

from zoo_tests.zoo_test_env import LINKED_DIR, ZOO_MAIN, Context, TestEnv

TOOLS_VENV = "tools/.venv"
VENV = "projects/shop/.venv"

SHOW_JAZZOO_FILE = "import jazzoo; print(jazzoo.__file__)"


def create_env(context: Context):
    return Env(context)


def test_linked_regular_install(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the venv tools, in which jazzoo 0.3.0 is installed as pip installs
    # it: the package and its dist-info in site-packages.
    if env.step(
        env.make_venv_with_installed_jazzoo(TOOLS_VENV, "0.3.0"),
    ):
        pass

    # We have the project shop. In its directory, we run the zoo of tools:
    # `zoo env --init --create-venv --without-pip`.
    #
    # The venv of shop should link the jazzoo package of tools, whose metadata
    # describes it, so the version should be 0.3.0.
    if env.step(
        env.write_project("shop"),
        env.run_zoo_of_venv(
            TOOLS_VENV,
            "env",
            "--init",
            "--create-venv",
            "--without-pip",
            cwd="projects/shop",
        ),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.dist_info_names(VENV) == ["jazzoo-0.3.0.dist-info"]
        assert env.read_direct_url(VENV)["url"] == (
            Path(env.site_packages(TOOLS_VENV), "jazzoo").as_uri()
        )

    # We ask the python of the venv of shop where it imports jazzoo from.
    #
    # It should import the jazzoo package of tools.
    if env.step(
        env.run_python_in_venv(VENV, SHOW_JAZZOO_FILE),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout.splitlines() == [
            os.path.join(env.site_packages(TOOLS_VENV), "jazzoo", "__init__.py")
        ]


class Env(TestEnv):
    def make_venv_with_installed_jazzoo(self, venv: str, version: str):
        """Creates a venv without pip, and installs a copy of the jazzoo package that
        runs the tests in it, with a dist-info as pip writes it."""
        subprocess.run(
            [sys.executable, "-m", "venv", "--without-pip", self.path(venv)],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=True,
        )
        site_packages = self.site_packages(venv)
        shutil.copytree(
            LINKED_DIR,
            os.path.join(site_packages, "jazzoo"),
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        dist_info = Path(site_packages, f"jazzoo-{version}.dist-info")
        dist_info.mkdir()
        (dist_info / "METADATA").write_text(
            f"Metadata-Version: 2.1\nName: jazzoo\nVersion: {version}\n",
            encoding="utf-8",
        )
        (dist_info / "INSTALLER").write_text("pip\n", encoding="utf-8")

    def run_zoo_of_venv(self, venv: str, *args: str, cwd: str = ""):
        """Runs zoo with the python of the venv, in a subprocess."""
        self.run_program(
            self.path(f"{venv}/bin/python"), "-c", ZOO_MAIN, *args, cwd=cwd
        )
