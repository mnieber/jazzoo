import json
import os
import subprocess
import sys

from zoo_tests.zoo_test_env import Context, TestEnv

from jazzoo.zoo.errors import JazzooLinkError, NoZooInVenvError

VENV = "projects/shop/.venv"


def create_env(context: Context):
    return Env(context)


def test_link_into_existing_venv(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the project shop, with a venv without jazzoo. ~/.local/bin is a
    # file, so zoo cannot write the link zoo-shop. We register shop.
    #
    # Writing the link fails after zoo linked jazzoo into the venv, so zoo should
    # remove the linked install again, and register nothing.
    if env.step(
        env.write_project("shop"),
        env.make_real_venv(VENV),
        env.remove_dir("home/.local/bin"),
        env.write_file("home/.local/bin", "not a directory\n"),
        env.init_env_and_catch_error("shop"),
    ):
        assert env.error is not None
        assert env.dist_info_names(VENV) == []
        assert not env.exists(env.path(f"{VENV}/bin/zoo"))
        assert not env.site_packages_names(VENV)
        assert not env.exists(env.env_dir("shop"))

    # We have the project blog, with a venv that has the dist-info of jazzoo but
    # no bin/zoo. We register blog.
    #
    # The install of jazzoo is broken, so this should raise a NoZooInVenvError,
    # and leave the venv alone.
    if env.step(
        env.write_project("blog"),
        env.make_fake_venv("projects/blog/.venv", with_zoo=False),
        env.make_dir("projects/blog/.venv/lib/python3.10/site-packages"),
        env.make_dir(
            "projects/blog/.venv/lib/python3.10/site-packages/jazzoo-0.3.0.dist-info"
        ),
        env.init_env_and_catch_error("blog"),
    ):
        assert isinstance(env.error, NoZooInVenvError)
        assert not env.exists(env.path("projects/blog/.venv/bin/zoo"))
        assert not env.exists(env.env_dir("blog"))
        assert not env.exists(env.zoo_link("blog"))

    # We have the project wiki, with a venv whose python is 3.8. We register
    # wiki.
    #
    # jazzoo needs a newer python, so this should raise a JazzooLinkError that
    # names both versions, and leave the venv alone.
    if env.step(
        env.write_project("wiki"),
        env.make_venv_with_old_python("projects/wiki/.venv", "3.8"),
        env.init_env_and_catch_error("wiki"),
    ):
        assert isinstance(env.error, JazzooLinkError)
        assert "3.8" in str(env.error)
        assert "3.10" in str(env.error)
        assert not env.site_packages_names("projects/wiki/.venv")
        assert not env.exists(env.path("projects/wiki/.venv/bin/zoo"))
        assert not env.exists(env.env_dir("wiki"))


class Env(TestEnv):
    def make_real_venv(self, venv: str):
        """Creates a venv without pip, in which nothing is installed."""
        subprocess.run(
            [sys.executable, "-m", "venv", "--without-pip", self.path(venv)],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=True,
        )

    def make_venv_with_old_python(self, venv: str, version: str):
        """Writes a fake venv whose bin/python only answers the question that zoo
        asks before it links jazzoo: where its site-packages is, and its version."""
        self.make_fake_venv(venv, with_zoo=False)
        site_packages = self.path(f"{venv}/lib/python{version}/site-packages")
        os.makedirs(site_packages)
        info = json.dumps(
            {"purelib": site_packages, "version": [int(x) for x in version.split(".")]}
        )
        self.write_executable(f"{venv}/bin/python", f"#!/bin/sh\necho '{info}'\n")

    def init_env_and_catch_error(self, name):
        self.error = None
        try:
            self.init_env(name)
        except Exception as error:
            self.error = error

    # Queries

    def site_packages_names(self, venv: str):
        """The names in the site-packages of the venv."""
        return sorted(os.listdir(self.site_packages(venv)))
