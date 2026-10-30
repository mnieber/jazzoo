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
    # package metadata, next to the package other.
    if env.step(
        env.copy_jazzoo_package(SRC_DIR),
        env.write_file(f"{SRC_DIR}/other/__init__.py", 'NAME = "other"\n'),
    ):
        pass

    # We have the project shop. In its directory, we run the zoo of the source
    # tree: `zoo env --init --create-venv --without-pip`.
    #
    # The linked jazzoo has no package metadata, so the version should be 0.0.0.
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
    pass
