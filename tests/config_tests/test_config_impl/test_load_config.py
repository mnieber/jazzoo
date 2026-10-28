import os

from config_tests.config_test_env import Context, TestEnv

from jazzoo import ExecutionError


def create_env(context: Context):
    return Env(context)


def test_load_config(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have some config files.
    if env.step(
        env.write_config("config/base.yaml", "root: {}\n"),
        env.write_config("a.yaml", "a: 1\n"),
        env.write_config("b.yaml", "b: 2\n"),
        env.write_config("pre.yaml", "pre: 0\n"),
    ):
        pass

    # From the tmp dir, we load a jazzoo file that loads a config file with a
    # relative path.
    #
    # The path should be resolved against the current working directory, and
    # JAZZOO_CONFIG_FILES should hold the absolute path.
    if env.step(
        env.write_file("relative.jaz", '⚙️.load_config(path="config/base.yaml")\n'),
        env.change_dir(),
        env.parse_module("relative.jaz"),
    ):
        assert env.config_files() == [env.path("config/base.yaml")]

    # We load a jazzoo file that loads two config files.
    #
    # JAZZOO_CONFIG_FILES should hold both, in the order of the calls, separated by
    # os.pathsep.
    if env.step(
        env.unset_env("JAZZOO_CONFIG_FILES"),
        env.write_file(
            "two.jaz",
            """
            ⚙️.load_config(path=⚙️.module.dirname / "a.yaml")
            ⚙️.load_config(path=⚙️.module.dirname / "b.yaml")
            """,
        ),
        env.parse_module("two.jaz"),
    ):
        assert env.env_var("JAZZOO_CONFIG_FILES") == os.pathsep.join(
            [env.path("a.yaml"), env.path("b.yaml")]
        )

    # We load a jazzoo file that loads a.yaml, b.yaml, and a.yaml again.
    #
    # a.yaml should be in the list once, at its first position.
    if env.step(
        env.unset_env("JAZZOO_CONFIG_FILES"),
        env.write_file(
            "twice.jaz",
            """
            ⚙️.load_config(path=⚙️.module.dirname / "a.yaml")
            ⚙️.load_config(path=⚙️.module.dirname / "b.yaml")
            ⚙️.load_config(path=⚙️.module.dirname / "a.yaml")
            """,
        ),
        env.parse_module("twice.jaz"),
    ):
        assert env.config_files() == [env.path("a.yaml"), env.path("b.yaml")]

    # We load a jazzoo file that loads a config file that does not exist.
    #
    # It should raise an ExecutionError.
    if env.step(
        env.unset_env("JAZZOO_CONFIG_FILES"),
        env.write_file(
            "missing.jaz",
            '⚙️.load_config(path=⚙️.module.dirname / "missing.yaml")\n',
        ),
        env.parse_module_and_catch_error("missing.jaz"),
    ):
        assert isinstance(env.error, ExecutionError)

    # We load a jazzoo file that loads a missing config file with required=false.
    #
    # Nothing should be added to the list.
    if env.step(
        env.write_file(
            "optional.jaz",
            '⚙️.load_config(path=⚙️.module.dirname / "missing.yaml", required=false)\n',
        ),
        env.parse_module("optional.jaz"),
    ):
        assert env.config_files() == []

    # We call a function that loads a config file in its body, between a line that
    # reads JAZZOO_CONFIG_FILES and a shell line that prints it.
    #
    # The load should take effect from its line on: the line before it sees no
    # config files, the shell line after it sees a.yaml.
    if env.step(
        env.unset_env("JAZZOO_CONFIG_FILES"),
        env.write_file(
            "body.jaz",
            """
            show():
                🐆.before = ⚙️.env.JAZZOO_CONFIG_FILES?:-unset
                ⚙️.load_config(path=⚙️.module.dirname / "a.yaml")
                echo "🐆.before $JAZZOO_CONFIG_FILES"
            """,
        ),
        env.parse_module("body.jaz"),
        env.evaluate("🐭.show()"),
    ):
        assert env.output == f"unset {env.path('a.yaml')}"

    # JAZZOO_CONFIG_FILES is already set when we load a jazzoo file that loads
    # a.yaml, like in a nested jaz call.
    #
    # The paths that were already set should stay at the start of the list.
    if env.step(
        env.set_env("JAZZOO_CONFIG_FILES", env.path("pre.yaml")),
        env.write_file(
            "nested.jaz",
            '⚙️.load_config(path=⚙️.module.dirname / "a.yaml")\n',
        ),
        env.parse_module("nested.jaz"),
    ):
        assert env.config_files() == [env.path("pre.yaml"), env.path("a.yaml")]


class Env(TestEnv):
    pass
