import csv
import importlib.metadata
import json
import os
import typing as T
from pathlib import Path

from zoo_tests.zoo_test_env import LINKED_DIR, Context, TestEnv

from jazzoo.zoo.actions.create_venv import CONSOLE_SCRIPTS

VENV = "projects/shop/.venv"

# The version of the jazzoo that runs the tests, and that the venv links
VERSION = importlib.metadata.version("jazzoo")

# Shows the distribution jazzoo, as importlib.metadata in the venv sees it
SHOW_DISTRIBUTION = """
import importlib.metadata, json
dist = importlib.metadata.distribution("jazzoo")
print(json.dumps({
    "name": dist.metadata["Name"],
    "version": dist.version,
    "console_scripts": {
        ep.name: ep.value for ep in dist.entry_points if ep.group == "console_scripts"
    },
}))
"""


def create_env(context: Context):
    return Env(context)


def test_linked_install_metadata(context: Context):
    # Create the test environment
    env = create_env(context)

    # We register the project shop with a new venv.
    if env.step(
        env.write_project("shop"),
        env.change_dir("projects/shop"),
        env.run_zoo("env", "--init", "--create-venv", "--without-pip"),
    ):
        pass

    # We look at the site-packages of the venv.
    #
    # It should have one dist-info of jazzoo, named after the version of the
    # linked jazzoo. pip list should show the real version, so there is no local
    # label (such as +linked).
    if env.step():
        assert env.dist_info_names(VENV) == [f"jazzoo-{VERSION}.dist-info"]

    # In the venv, we read the distribution jazzoo with importlib.metadata.
    #
    # It should have the name and the version of the linked jazzoo, and the
    # console scripts of jazzoo as its entry points.
    if env.step(
        env.run_python_in_venv(VENV, SHOW_DISTRIBUTION),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert json.loads(env.completed.stdout) == {
            "name": "jazzoo",
            "version": VERSION,
            "console_scripts": {
                name: f"{module}:main" for name, module in CONSOLE_SCRIPTS.items()
            },
        }

    # We look at INSTALLER and direct_url.json.
    #
    # INSTALLER should name zoo, and direct_url.json should point to the linked
    # directory, as an editable install.
    if env.step():
        assert env.read_file(env.dist_info_file(VENV, "INSTALLER")) == "zoo\n"
        assert env.read_direct_url(VENV) == {
            "url": Path(LINKED_DIR).as_uri(),
            "dir_info": {"editable": True},
        }

    # We look at the paths in RECORD.
    #
    # They should be exactly the files that zoo wrote for the link: pip uninstall
    # removes these files, so nothing of the linked directory may be among them.
    if env.step():
        assert sorted(env.record_paths(VENV)) == sorted(
            [
                os.path.join(env.site_packages(VENV), "_jazzoo_link.pth"),
                os.path.join(env.site_packages(VENV), "_jazzoo_link.py"),
                env.dist_info_file(VENV, "METADATA"),
                env.dist_info_file(VENV, "INSTALLER"),
                env.dist_info_file(VENV, "entry_points.txt"),
                env.dist_info_file(VENV, "direct_url.json"),
                env.dist_info_file(VENV, "RECORD"),
            ]
            + [env.path(f"{VENV}/bin/{name}") for name in CONSOLE_SCRIPTS]
        )
        assert not [
            path
            for path in env.record_paths(VENV)
            if path.startswith(LINKED_DIR + os.sep)
        ]


class Env(TestEnv):
    # Queries

    def record_paths(self, venv: str) -> T.List[str]:
        """The paths in RECORD, as absolute paths (they are relative to
        site-packages)."""
        with open(self.dist_info_file(venv, "RECORD"), newline="") as f:
            return [
                os.path.normpath(os.path.join(self.site_packages(venv), row[0]))
                for row in csv.reader(f)
                if row
            ]
