import importlib.metadata
import os

from zoo_tests.zoo_test_env import LINKED_DIR, Context, TestEnv

SCRIPTS = ["zoo", "jaz", "jazzoo", "jaz-run"]

VENV = "projects/shop/.venv"

# Shows where the venv imports jazzoo from, and which version it sees
SHOW_JAZZOO = """
import importlib.metadata, jazzoo
print(jazzoo.__file__)
print(importlib.metadata.version("jazzoo"))
"""


def create_env(context: Context):
    return Env(context)


def test_create_a_venv(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a project shop without a venv. In its directory, we run
    # `zoo env --init --create-venv --without-pip`.
    #
    # zoo should create the venv .venv, with the name of the env as its prompt,
    # and register it.
    if env.step(
        env.write_project("shop"),
        env.change_dir("projects/shop"),
        env.run_zoo("env", "--init", "--create-venv", "--without-pip"),
    ):
        assert env.is_dir(env.path("projects/shop/.venv"))
        assert env.venv_prompt("projects/shop/.venv") == "shop"
        assert env.read_link(env.env_dir("shop") + "/venv_dir") == env.path(
            "projects/shop/.venv"
        )
        assert env.output == env.source_line("shop")

    # We look at the venv, and ask its python where it imports jazzoo from.
    #
    # The jazzoo package that runs these tests should be linked into the venv as
    # a linked install: an import hook and package metadata, not a symlink. The
    # venv should see the version of the linked jazzoo, and the console scripts
    # of jazzoo should run with the python of the venv.
    if env.step(
        env.run_python_in_venv(VENV, SHOW_JAZZOO),
    ):
        assert not env.exists(env.site_packages(VENV) + "/jazzoo")
        assert env.exists(env.site_packages(VENV) + "/_jazzoo_link.pth")
        assert env.exists(env.site_packages(VENV) + "/_jazzoo_link.py")
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout.splitlines() == [
            os.path.join(LINKED_DIR, "__init__.py"),
            importlib.metadata.version("jazzoo"),
        ]
        for script in SCRIPTS:
            path = env.path(f"projects/shop/.venv/bin/{script}")
            assert os.access(path, os.X_OK), script
            assert env.read_lines(path)[0] == (
                "#!" + env.path("projects/shop/.venv/bin/python")
            ), script

    # In another directory, we run `.venv/bin/zoo where` as a program.
    #
    # The zoo of the venv should find shop through its own sys.prefix, and run
    # the target in the project directory.
    if env.step(
        env.make_dir("elsewhere"),
        env.run_program(
            env.path("projects/shop/.venv/bin/zoo"), "where", cwd="elsewhere"
        ),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout.splitlines() == [
            "cwd=" + env.path("projects/shop"),
            "invocation_dir=" + env.path("elsewhere"),
        ]

    # We run `zoo-shop where`, through the link in ~/.local/bin.
    #
    # The link runs the same zoo, so the result should be the same.
    if env.step(
        env.run_program(env.zoo_link("shop"), "where", cwd="elsewhere"),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout.splitlines()[0] == "cwd=" + env.path(
            "projects/shop"
        )


class Env(TestEnv):
    # Queries

    def venv_prompt(self, venv: str) -> str:
        for line in self.read_lines(self.path(f"{venv}/pyvenv.cfg")):
            key, _, value = line.partition("=")
            if key.strip() == "prompt":
                return value.strip().strip("'\"")
        return ""
