from interactive_tests.interactive_test_env import Context, TestEnv

JAZZOO_SOURCE = """
deploy():
    [interactive]
    🐆.build():
        @echo "building the images"

    🐆.version():
        @echo "1.2.3"

    🐆.build()
    🐆.v = 🐆.version()
    🐆.retval = 🐆.v
"""


def create_env(context: Context):
    return Env(context)


def test_interactive_step_in_a_function(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a deploy function with an interactive local function that builds, and
    # a captured local function that reports the version. We run deploy.
    #
    # The build output should go to the console, and the version should be
    # returned. The build output should not be part of the result.
    if env.step(
        env.write_file("jazzoo", JAZZOO_SOURCE),
        env.parse_module("jazzoo"),
        env.evaluate("🐭.deploy()"),
        env.read_printed(),
    ):
        assert "building the images" in env.printed.splitlines()
        assert env.output == "1.2.3"


class Env(TestEnv):
    pass
