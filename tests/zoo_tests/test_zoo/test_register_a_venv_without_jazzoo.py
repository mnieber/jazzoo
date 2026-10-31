import os
import subprocess
import sys

from zoo_tests.zoo_test_env import LINKED_DIR, Context, TestEnv

from jazzoo.zoo.actions.link_jazzoo import CONSOLE_SCRIPTS

VENV = "projects/shop/.env"

SHOW_JAZZOO_FILE = "import jazzoo; print(jazzoo.__file__)"


def create_env(context: Context):
    return Env(context)


def test_register_a_venv_without_jazzoo(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the project shop, with a venv in .env that has neither pip nor
    # jazzoo. In the project directory, we run `zoo env --init --venv-path .env`.
    #
    # zoo should give the venv a linked install of jazzoo, as --create-venv does,
    # and say so on stderr. The zoo link should point to the new zoo of the venv.
    if env.step(
        env.write_project("shop"),
        env.make_real_venv(VENV),
        env.change_dir("projects/shop"),
        env.run_zoo("env", "--init", "--venv-path", ".env"),
    ):
        assert env.output == env.source_line("shop")
        assert (
            f"zoo: linked the jazzoo in {LINKED_DIR} into the venv {env.path(VENV)}"
            in env.printed_err
        )
        assert len(env.dist_info_names(VENV)) == 1
        for name in CONSOLE_SCRIPTS:
            assert env.exists(env.path(f"{VENV}/bin/{name}"))
        assert env.read_link(env.zoo_link("shop")) == env.path(f"{VENV}/bin/zoo")

    # We ask the python of the venv where it imports jazzoo from.
    #
    # It should import the jazzoo that ran zoo.
    if env.step(
        env.run_python_in_venv(VENV, SHOW_JAZZOO_FILE),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout.splitlines() == [
            os.path.join(LINKED_DIR, "__init__.py")
        ]


class Env(TestEnv):
    def make_real_venv(self, venv: str):
        """Creates a venv without pip, in which nothing is installed."""
        subprocess.run(
            [sys.executable, "-m", "venv", "--without-pip", self.path(venv)],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=True,
        )
