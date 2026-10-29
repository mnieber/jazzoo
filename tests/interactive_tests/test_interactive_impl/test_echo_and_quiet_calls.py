import sys

from interactive_tests.interactive_test_env import Context, TestEnv

from jazzoo import get_targets

JAZZOO_SOURCE = f"""
[interactive]
build():
    echo "building"
    @echo "done"

[interactive]
script():
    #!{sys.executable}
    print("from python")

[private]
[interactive]
_helper():
    @echo "helping"
"""

QUIETLY_SOURCE = """
[interactive]
live():
    echo "live output"

quietly():
    🐆.retval = 🐭.live()
"""


def create_env(context: Context):
    return Env(context)


def test_echo_and_quiet_calls(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have an interactive function with a shell line, and a shell line with @.
    # We run it.
    #
    # The first line should be echoed before its output, and the @ line should not
    # be echoed.
    if env.step(
        env.write_file("build.jaz", JAZZOO_SOURCE),
        env.parse_module("build.jaz"),
        env.evaluate("🐭.build()"),
        env.read_printed(),
    ):
        assert env.printed == 'echo "building"\nbuilding\ndone\n'

    # We run an interactive function with a Python block.
    #
    # The block should not be echoed; only its output is printed.
    if env.step(
        env.evaluate("🐭.script()"),
        env.read_printed(),
    ):
        assert env.printed == "from python\n"

    # We have a function that calls an interactive function quietly, by assigning
    # its value. We run it.
    #
    # The interactive function should still print its output, but its shell line
    # should not be echoed, as in any quiet call. Its value should be empty.
    if env.step(
        env.write_file("quietly.jaz", QUIETLY_SOURCE),
        env.parse_module("quietly.jaz"),
        env.evaluate("🐭.quietly()"),
        env.read_printed(),
    ):
        assert env.printed == "live output\n"
        assert env.output == ""

    # We look at the targets of build.jaz, which has a function that is both
    # private and interactive.
    #
    # It should not be a target, and calling it should still be interactive.
    if env.step(
        env.parse_module("build.jaz"),
        env.evaluate("🐭._helper()"),
        env.read_printed(),
    ):
        assert "_helper" not in env.target_names()
        assert env.printed == "helping\n"
        assert env.output == ""


class Env(TestEnv):
    # Queries

    def target_names(self):
        return [function.name for function in get_targets(self.root_module)]
