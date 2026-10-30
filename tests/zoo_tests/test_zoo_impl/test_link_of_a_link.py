import os
from pathlib import Path

from zoo_tests.zoo_test_env import LINKED_DIR, Context, TestEnv

SHOW_JAZZOO_FILE = "import jazzoo; print(jazzoo.__file__)"


def create_env(context: Context):
    return Env(context)


def test_link_of_a_link(context: Context):
    # Create the test environment
    env = create_env(context)

    # We register the project shop with a new venv, which links the jazzoo that
    # runs the tests.
    if env.step(
        env.write_project("shop"),
        env.change_dir("projects/shop"),
        env.run_zoo("env", "--init", "--create-venv", "--without-pip"),
    ):
        pass

    # We have the project blog. In its directory, we run the zoo of the venv of
    # shop: `zoo env --init --create-venv --without-pip`.
    #
    # zoo should create the venv of blog.
    if env.step(
        env.write_project("blog"),
        env.run_program(
            env.path("projects/shop/.venv/bin/zoo"),
            "env",
            "--init",
            "--create-venv",
            "--without-pip",
            cwd="projects/blog",
        ),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.is_dir(env.path("projects/blog/.venv"))

    # We look at the venv of blog, and ask its python where it imports jazzoo
    # from.
    #
    # It should link the same directory as the venv of shop, and not the
    # site-packages of shop: a link, not a link to a link.
    if env.step(
        env.run_python_in_venv("projects/blog/.venv", SHOW_JAZZOO_FILE),
    ):
        assert env.read_direct_url("projects/blog/.venv")["url"] == (
            Path(LINKED_DIR).as_uri()
        )
        assert not env.exists(env.site_packages("projects/blog/.venv") + "/jazzoo")
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout.splitlines() == [
            os.path.join(LINKED_DIR, "__init__.py")
        ]


class Env(TestEnv):
    pass
