from zoo_tests.zoo_test_env import Context, TestEnv

from jazzoo.zoo.errors import (
    InvalidZooEnvNameError,
    NoRootFileError,
    NotAVenvError,
    NoZooInVenvError,
    VenvInUseError,
    ZooEnvExistsError,
    ZooLinkExistsError,
)


def create_env(context: Context):
    return Env(context)


def test_init_errors(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the registered project "shop".
    if env.step(
        env.add_project("shop"),
        env.init_env("shop"),
    ):
        pass

    # We register another project under the name shop.
    #
    # The name is taken, so this should raise a ZooEnvExistsError, and leave the
    # registered shop alone.
    if env.step(
        env.add_project("shop2"),
        env.init_env_and_catch_error("shop", project="projects/shop2"),
    ):
        assert isinstance(env.error, ZooEnvExistsError)
        assert env.read_link(env.env_dir("shop") + "/root_dir") == env.path(
            "projects/shop"
        )

    # We register projects under names that break the rules for names.
    #
    # Each should raise an InvalidZooEnvNameError, and register nothing.
    for name in ["my env", ".x", "a/b"]:
        if env.step(
            env.init_env_and_catch_error(name, project="projects/shop2"),
        ):
            assert isinstance(env.error, InvalidZooEnvNameError)
            assert not env.exists(env.env_dir(name))
            assert not env.exists(env.zoo_link(name))

    # We register a project under a name with a dash, an underscore, a digit and
    # a dot.
    #
    # Those are allowed.
    if env.step(
        env.init_env("my-env_2.0", project="projects/shop2"),
    ):
        assert env.is_dir(env.env_dir("my-env_2.0"))

    # We register a directory without a jazzoo file.
    #
    # It has no root module, so this should raise a NoRootFileError.
    if env.step(
        env.make_fake_venv("projects/empty/.venv"),
        env.init_env_and_catch_error("empty"),
    ):
        assert isinstance(env.error, NoRootFileError)
        assert not env.exists(env.env_dir("empty"))
        assert not env.exists(env.zoo_link("empty"))

    # We add a jazzoo.jaz file to that directory, and register it again.
    #
    # jazzoo.jaz is a root file too, so this should work.
    if env.step(
        env.write_file("projects/empty/jazzoo.jaz", "build():\n    echo build\n"),
        env.init_env("empty"),
    ):
        assert env.is_dir(env.env_dir("empty"))

    # We register a project with a directory that is not a venv.
    #
    # It has no pyvenv.cfg, so this should raise a NotAVenvError.
    if env.step(
        env.write_project("docs"),
        env.write_file("projects/docs/not-a-venv/bin/zoo", ""),
        env.init_env_and_catch_error("docs", venv="projects/docs/not-a-venv"),
    ):
        assert isinstance(env.error, NotAVenvError)
        assert not env.exists(env.env_dir("docs"))

    # We register a project with a venv path that does not exist, as if we forgot
    # --create-venv.
    #
    # This should raise a NotAVenvError that suggests --create-venv, and create
    # nothing.
    if env.step(
        env.write_project("wiki"),
        env.init_env_and_catch_error("wiki", venv="projects/wiki/venvs/wiki"),
    ):
        assert isinstance(env.error, NotAVenvError)
        assert "--create-venv" in str(env.error)
        assert not env.exists(env.env_dir("wiki"))
        assert not env.exists(env.path("projects/wiki/venvs"))

    # We register a project with a venv that has no zoo.
    #
    # Jazzoo is not installed in it, so this should raise a NoZooInVenvError.
    if env.step(
        env.make_fake_venv("projects/docs/.venv", with_zoo=False),
        env.init_env_and_catch_error("docs"),
    ):
        assert isinstance(env.error, NoZooInVenvError)
        assert not env.exists(env.env_dir("docs"))

    # We register a project with the venv of shop.
    #
    # A venv belongs to at most one env, so this should raise a VenvInUseError.
    if env.step(
        env.init_env_and_catch_error("docs", venv="projects/shop/.venv"),
    ):
        assert isinstance(env.error, VenvInUseError)
        assert not env.exists(env.env_dir("docs"))
        assert not env.exists(env.zoo_link("docs"))

    # We have a file of our own at ~/.local/bin/zoo-blog, and register the
    # project blog.
    #
    # zoo never overwrites a file, so this should raise a ZooLinkExistsError, and
    # leave the file untouched.
    if env.step(
        env.add_project("blog"),
        env.write_file("home/.local/bin/zoo-blog", "my own script\n"),
        env.init_env_and_catch_error("blog"),
    ):
        assert isinstance(env.error, ZooLinkExistsError)
        assert not env.exists(env.env_dir("blog"))
        assert not env.is_link(env.zoo_link("blog"))
        assert env.read_file(env.zoo_link("blog")) == "my own script\n"


class Env(TestEnv):
    def init_env_and_catch_error(self, name, project=None, venv=None):
        self.error = None
        try:
            self.init_env(name, project=project, venv=venv)
        except Exception as error:
            self.error = error
