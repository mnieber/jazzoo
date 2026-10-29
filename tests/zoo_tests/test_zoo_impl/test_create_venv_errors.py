import os

import pytest
from zoo_tests.zoo_test_env import Context, TestEnv

from jazzoo.zoo.errors import VenvCreationError, VenvExistsError


def create_env(context: Context):
    return Env(context)


# root can write to a read-only directory, so venv creation would not fail
@pytest.mark.skipif(os.geteuid() == 0, reason="runs as root")
def test_create_venv_errors(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a project shop that already has a .venv directory, and run
    # `zoo env --init --create-venv` in it.
    #
    # zoo does not touch an existing venv, so this should raise a
    # VenvExistsError, and register nothing.
    if env.step(
        env.write_project("shop"),
        env.write_file("projects/shop/.venv/marker.txt", "mine\n"),
        env.change_dir("projects/shop"),
        env.run_zoo_and_catch_error("env", "--init", "--create-venv", "--without-pip"),
    ):
        assert isinstance(env.error, VenvExistsError)
        assert not env.exists(env.env_dir("shop"))
        assert env.read_file(env.path("projects/shop/.venv/marker.txt")) == "mine\n"

    # We have a project blog in a read-only directory, and run
    # `zoo env --init --create-venv` in it.
    #
    # The venv cannot be created, so this should raise a VenvCreationError, and
    # leave nothing behind: no env directory and no zoo-blog link.
    if env.step(
        env.write_project("blog"),
        env.make_read_only("projects/blog"),
        env.change_dir("projects/blog"),
        env.run_zoo_and_catch_error("env", "--init", "--create-venv", "--without-pip"),
    ):
        assert isinstance(env.error, VenvCreationError)
        assert not env.exists(env.env_dir("blog"))
        assert not env.exists(env.zoo_link("blog"))
        assert not env.exists(env.path("projects/blog/.venv"))

    # We make the directory writable again, so that tmp_path can be removed.
    if env.step(
        env.make_writable("projects/blog"),
    ):
        pass


class Env(TestEnv):
    def make_read_only(self, name: str):
        os.chmod(self.path(name), 0o555)

    def make_writable(self, name: str):
        os.chmod(self.path(name), 0o755)
