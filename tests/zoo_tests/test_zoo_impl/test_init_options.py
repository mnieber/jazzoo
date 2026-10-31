import os

from zoo_tests.zoo_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_init_options(context: Context):
    # Create the test environment
    env = create_env(context)

    # We register the project shop under an explicit name.
    #
    # The env should get that name, not the name of the directory.
    if env.step(
        env.add_project("shop"),
        env.init_env("shop-dev", project="projects/shop"),
    ):
        assert env.is_dir(env.env_dir("shop-dev"))
        assert not env.exists(env.env_dir("shop"))
        assert env.output == env.source_line("shop-dev")

    # We register the project blog with a relative path to its venv.
    #
    # The link to the venv should be absolute, so that it works from any
    # directory.
    if env.step(
        env.add_project("blog"),
        env.change_dir("projects/blog"),
        env.run_zoo("env", "--init", "--venv-path", "./.venv"),
    ):
        assert env.read_link(env.env_dir("blog") + "/venv_dir") == env.path(
            "projects/blog/.venv"
        )

    # We set XDG_CONFIG_HOME, and register the project docs.
    #
    # The registry should be in $XDG_CONFIG_HOME/jazzoo, and not in ~/.config.
    if env.step(
        env.set_env("XDG_CONFIG_HOME", env.path("xdg")),
        env.add_project("docs"),
        env.init_env("docs"),
    ):
        assert env.is_dir(env.path("xdg/jazzoo/envs/docs"))
        assert not env.exists(env.env_dir("docs"))

    # We take ~/.local/bin off the PATH, and register the project wiki.
    #
    # The zoo-wiki link cannot be found then, so zoo should say so on stderr, but
    # register the env anyway.
    if env.step(
        env.unset_env("XDG_CONFIG_HOME"),
        env.remove_local_bin_from_path(),
        env.add_project("wiki"),
        env.init_env("wiki"),
    ):
        assert env.is_dir(env.env_dir("wiki"))
        assert env.is_link(env.zoo_link("wiki"))
        assert env.path("home/.local/bin") in env.printed_err
        assert "PATH" in env.printed_err

    # We have a zoo-news link that already points to the zoo of the venv of the
    # project news, and register news.
    #
    # The link is the one that zoo would create, so this should work.
    if env.step(
        env.add_project("news"),
        env.make_link(env.path("projects/news/.venv/bin/zoo"), env.zoo_link("news")),
        env.init_env("news"),
    ):
        assert env.is_dir(env.env_dir("news"))
        assert env.read_link(env.zoo_link("news")) == env.path(
            "projects/news/.venv/bin/zoo"
        )


class Env(TestEnv):
    def remove_local_bin_from_path(self):
        local_bin = self.path("home/.local/bin")
        dirs = os.environ["PATH"].split(os.pathsep)
        self.set_env("PATH", os.pathsep.join(d for d in dirs if d != local_bin))

    def make_link(self, target: str, path: str):
        os.symlink(target, path)
