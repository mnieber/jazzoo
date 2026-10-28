import sys

from config_tests.config_test_env import Context, TestEnv

JAZZOO_SOURCE = f"""
    ⚙️.load_config(path=⚙️.module.dirname / "config/base.yaml")
    ⚙️.load_config(path=⚙️.module.dirname / "config/local.yaml", required=false)

    build:
        #!{sys.executable}
        from jazzoo import get_config as get

        print(get("/root/src"))
    """


def create_env(context: Context):
    return Env(context)


def test_jazzoo_script_reads_config(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a base config file, and a jazzoo file that loads it, and also loads
    # an optional local config file that does not exist yet. Its build target runs
    # a Python block that reads the source dir.
    #
    # The Python block should print the source dir of the base config.
    if env.step(
        env.write_config("config/base.yaml", "root:\n  src: /home/jane/shop/src\n"),
        env.write_file("jazzoo", JAZZOO_SOURCE),
        env.parse_module("jazzoo"),
        env.evaluate("🐭.build()"),
    ):
        assert env.output == "/home/jane/shop/src"

    # We add the local config file, which sets another source dir, and load the
    # jazzoo file again.
    #
    # The Python block should print the source dir of the local config.
    if env.step(
        env.write_config("config/local.yaml", "root:\n  src: /srv/shop/src\n"),
        env.parse_module("jazzoo"),
        env.evaluate("🐭.build()"),
    ):
        assert env.output == "/srv/shop/src"


class Env(TestEnv):
    pass
