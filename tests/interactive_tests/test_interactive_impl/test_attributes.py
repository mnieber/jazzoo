from interactive_tests.interactive_test_env import Context, TestEnv

from jazzoo import ParseError, get_targets

MISSPELLED_SOURCE = """
build():
    @echo "building"

[interactve]
shell():
    @echo "shell"
"""

MISSPELLED_LOCAL_SOURCE = """
deploy():
    [interactve]
    🐆.build():
        @echo "building"

    🐆.build()
"""

PRIVATE_LOCAL_SOURCE = """
deploy():
    [private]
    🐆.build():
        @echo "building"

    🐆.build()
"""

TEST_COMMAND_SOURCE = """
check():
    [ -d / ]
    @echo "checked"
"""

STACKED_SOURCE = """
[private]
[interactive]
_shell():
    @echo "shell"

[interactive]
[private]
_other_shell():
    @echo "other shell"
"""


def create_env(context: Context):
    return Env(context)


def test_attributes(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a jazzoo file with a misspelled attribute. We load it.
    #
    # It should raise a ParseError that names the attribute and its line.
    if env.step(
        env.write_file("misspelled.jaz", MISSPELLED_SOURCE),
        env.parse_module_and_catch_error("misspelled.jaz"),
    ):
        assert isinstance(env.error, ParseError)
        assert "interactve" in str(env.error)
        assert env.error.line == 4

    # We have a jazzoo file with a misspelled attribute before a local function. We
    # load it.
    #
    # It should raise a ParseError.
    if env.step(
        env.write_file("misspelled_local.jaz", MISSPELLED_LOCAL_SOURCE),
        env.parse_module_and_catch_error("misspelled_local.jaz"),
    ):
        assert isinstance(env.error, ParseError)
        assert "interactve" in str(env.error)

    # We have a jazzoo file with [private] before a local function. We load it.
    #
    # It should raise a ParseError: a local function is never a target.
    if env.step(
        env.write_file("private_local.jaz", PRIVATE_LOCAL_SOURCE),
        env.parse_module_and_catch_error("private_local.jaz"),
    ):
        assert isinstance(env.error, ParseError)
        assert "private" in str(env.error)

    # We have a function with a shell line that looks like an attribute, but is not
    # followed by a local function. We run it.
    #
    # The line should be an ordinary shell line, as before.
    if env.step(
        env.write_file("test_command.jaz", TEST_COMMAND_SOURCE),
        env.parse_module("test_command.jaz"),
        env.evaluate("🐭.check()"),
    ):
        assert env.output == "checked"

    # We have functions with two attributes on separate lines, in both orders. We
    # load the file and run them.
    #
    # Both attributes should apply: the functions are interactive (they return
    # nothing) and they are not targets.
    if env.step(
        env.write_file("stacked.jaz", STACKED_SOURCE),
        env.parse_module("stacked.jaz"),
        env.evaluate("🐭._shell()"),
        env.evaluate("🐭._other_shell()", store_as="other_output"),
    ):
        assert env.output == ""
        assert env.other_output == ""
        assert env.target_names() == []


class Env(TestEnv):
    def __post_init__(self):
        super().__post_init__()
        self.other_output = None

    # Queries

    def target_names(self):
        return [function.name for function in get_targets(self.root_module)]
