from zoo_tests.zoo_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_register_a_project(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a project "shop" with a jazzoo file and a venv in .venv. In the
    # project directory, we run `zoo env --init --venv-path .venv`.
    #
    # The env should be called "shop", after the directory. Its directory in the
    # registry should link to the project and the venv, and zoo should print the
    # line that activates it.
    if env.step(
        env.add_project("shop"),
        env.change_dir("projects/shop"),
        env.run_zoo("env", "--init", "--venv-path", ".venv"),
    ):
        assert env.is_dir(env.env_dir("shop"))
        assert env.read_link(env.env_dir("shop") + "/root_dir") == env.path(
            "projects/shop"
        )
        assert env.read_link(env.env_dir("shop") + "/venv_dir") == env.path(
            "projects/shop/.venv"
        )
        assert env.output == env.source_line("shop")

    # We look at ~/.local/bin.
    #
    # It should have the link zoo-shop to the zoo of the venv, so that
    # `zoo-shop` runs the targets of shop.
    if env.step():
        assert env.read_link(env.zoo_link("shop")) == env.path(
            "projects/shop/.venv/bin/zoo"
        )

    # We register a second project "blog" in the same way.
    if env.step(
        env.add_project("blog"),
        env.init_env("blog"),
    ):
        pass

    # We list the envs.
    #
    # Both should be listed, sorted by name, with their root directories.
    if env.step(
        env.run_zoo("env", "--list"),
    ):
        assert env.output.splitlines() == [
            "  blog  " + env.path("projects/blog"),
            "  shop  " + env.path("projects/shop"),
        ]


class Env(TestEnv):
    pass
