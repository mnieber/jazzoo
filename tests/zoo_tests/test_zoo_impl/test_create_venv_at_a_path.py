from zoo_tests.zoo_test_env import Context, TestEnv

from jazzoo.zoo.errors import VenvExistsError

SHOP_VENV = "projects/shop/path/to/new/my_venv"
BLOG_VENV = "venvs/blog"


def create_env(context: Context):
    return Env(context)


def test_create_venv_at_a_path(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a project shop without a venv. In its directory, we run
    # `zoo env --init --create-venv --venv-path=./path/to/new/my_venv --without-pip`.
    #
    # zoo should create the venv at that path, together with the directories
    # above it, and register it with an absolute link. The project should get no
    # .venv.
    if env.step(
        env.write_project("shop"),
        env.change_dir("projects/shop"),
        env.run_zoo(
            "env",
            "--init",
            "--create-venv",
            "--venv-path=./path/to/new/my_venv",
            "--without-pip",
        ),
    ):
        assert env.exists(env.path(f"{SHOP_VENV}/pyvenv.cfg"))
        assert env.venv_prompt(SHOP_VENV) == "shop"
        assert env.read_link(env.env_dir("shop") + "/venv_dir") == env.path(SHOP_VENV)
        assert env.read_link(env.zoo_link("shop")) == env.path(f"{SHOP_VENV}/bin/zoo")
        assert not env.exists(env.path("projects/shop/.venv"))
        assert env.output == env.source_line("shop")

    # We have a project blog without a venv. In its directory, we run
    # `zoo env --init blog --create-venv --venv-path <tmp>/venvs/blog --without-pip`.
    #
    # The path is a separate word here, and absolute. zoo should create the venv
    # there, and register it.
    if env.step(
        env.write_project("blog"),
        env.change_dir("projects/blog"),
        env.run_zoo(
            "env",
            "--init",
            "blog",
            "--create-venv",
            "--venv-path",
            env.path(BLOG_VENV),
            "--without-pip",
        ),
    ):
        assert env.venv_prompt(BLOG_VENV) == "blog"
        assert env.read_link(env.env_dir("blog") + "/venv_dir") == env.path(BLOG_VENV)

    # We have a project news. In its directory, we run
    # `zoo env --init --create-venv --venv-path=<tmp>/venvs/blog`.
    #
    # The venv of blog is there, and zoo does not touch an existing venv, so this
    # should raise a VenvExistsError, and register nothing.
    if env.step(
        env.write_project("news"),
        env.change_dir("projects/news"),
        env.run_zoo_and_catch_error(
            "env",
            "--init",
            "--create-venv",
            f"--venv-path={env.path(BLOG_VENV)}",
            "--without-pip",
        ),
    ):
        assert isinstance(env.error, VenvExistsError)
        assert not env.exists(env.env_dir("news"))
        assert env.venv_prompt(BLOG_VENV) == "blog"


class Env(TestEnv):
    # Queries

    def venv_prompt(self, venv: str) -> str:
        for line in self.read_lines(self.path(f"{venv}/pyvenv.cfg")):
            key, _, value = line.partition("=")
            if key.strip() == "prompt":
                return value.strip().strip("'\"")
        return ""
