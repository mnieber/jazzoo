from interactive_tests.interactive_test_env import Context, TestEnv

from jazzoo import ParseError, get_targets

LIST_SOURCE = """
[private, interactive]
_shell():
    @echo "shell"

[interactive, private]
_other_shell():
    @echo "other shell"
"""

NO_SPACES_SOURCE = """
[private,interactive]
_shell():
    @echo "shell"
"""

EXTRA_SPACES_SOURCE = """
[private , interactive ]
_shell():
    @echo "shell"
"""

MIXED_SOURCE = """
[interactive]
[private]
_shell():
    @echo "shell"

[private, interactive]
[private]
_other_shell():
    @echo "other shell"
"""

REPEATED_SOURCE = """
build():
    @echo "building"

[private, private]
_helper():
    @echo "helping"
"""

MISSPELLED_SOURCE = """
build():
    @echo "building"

[private, interactve]
_shell():
    @echo "shell"
"""

TRAILING_COMMA_SOURCE = """
build():
    @echo "building"

[private,]
_shell():
    @echo "shell"
"""

EMPTY_ITEM_SOURCE = """
build():
    @echo "building"

[private,,interactive]
_shell():
    @echo "shell"
"""

MISSING_COMMA_SOURCE = """
build():
    @echo "building"

[private interactive]
_shell():
    @echo "shell"
"""

LOCAL_LIST_SOURCE = """
deploy():
    [interactive, interactive]
    🐆.build():
        @echo "building the images"

    🐆.version():
        @echo "1.2.3"

    🐆.build()
    🐆.v = 🐆.version()
    🐆.retval = 🐆.v
"""

LOCAL_PRIVATE_SOURCE = """
deploy():
    [interactive, private]
    🐆.build():
        @echo "building the images"

    🐆.build()
"""

LOCAL_TRAILING_COMMA_SOURCE = """
deploy():
    [interactive,]
    🐆.build():
        @echo "building the images"

    🐆.build()
"""

BODY_ATTRIBUTE_SOURCE = """
deploy():
    [interactive]
    @echo "deploying"
"""

BODY_MISSPELLED_SOURCE = """
deploy():
    [interactve]
    @echo "deploying"
"""

TOP_LEVEL_BEFORE_ASSIGNMENT_SOURCE = """
build():
    @echo "building"

[private]
🐭.mode = "release"
"""

TOP_LEVEL_AT_END_SOURCE = """
build():
    @echo "building"

[private]
"""

SHELL_TESTS_SOURCE = """
check():
    [ -d / ]
    [[ -d / ]]
    [ "a,b" = "a,b" ]
    [ private ]
    🐆.done():
        @echo "checked"

    🐆.out = 🐆.done()
    🐆.retval = 🐆.out
"""


def create_env(context: Context):
    return Env(context)


def test_attribute_lists(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have functions with the attribute list [private, interactive], in both
    # orders. We load the file and run them.
    #
    # Both attributes should apply: the functions print to the console and return
    # nothing, and they are not targets.
    if env.step(
        env.write_file("list.jaz", LIST_SOURCE),
        env.parse_module("list.jaz"),
        env.evaluate("🐭._shell()"),
        env.evaluate("🐭._other_shell()", store_as="other_output"),
        env.read_printed(),
    ):
        assert env.output == ""
        assert env.other_output == ""
        assert env.printed.splitlines() == ["shell", "other shell"]
        assert env.target_names() == []

    # We have a function with the attribute list [private,interactive], without
    # spaces. We load the file and run it.
    #
    # Both attributes should apply.
    if env.step(
        env.write_file("no_spaces.jaz", NO_SPACES_SOURCE),
        env.parse_module("no_spaces.jaz"),
        env.evaluate("🐭._shell()"),
        env.read_printed(),
    ):
        assert env.output == ""
        assert env.printed.splitlines() == ["shell"]
        assert env.target_names() == []

    # We have a function with the attribute list [private , interactive ], with
    # spaces before the comma and the closing bracket. We load the file and run it.
    #
    # Both attributes should apply.
    if env.step(
        env.write_file("extra_spaces.jaz", EXTRA_SPACES_SOURCE),
        env.parse_module("extra_spaces.jaz"),
        env.evaluate("🐭._shell()"),
        env.read_printed(),
    ):
        assert env.output == ""
        assert env.printed.splitlines() == ["shell"]
        assert env.target_names() == []

    # We have functions whose attributes are spread over several lines, with and
    # without a list. We load the file and run them.
    #
    # All the attributes should apply.
    if env.step(
        env.write_file("mixed.jaz", MIXED_SOURCE),
        env.parse_module("mixed.jaz"),
        env.evaluate("🐭._shell()"),
        env.evaluate("🐭._other_shell()", store_as="other_output"),
        env.read_printed(),
    ):
        assert env.output == ""
        assert env.other_output == ""
        assert env.printed.splitlines() == ["shell", "other shell"]
        assert env.target_names() == []

    # We have a function with the attribute list [private, private]. We load the
    # file.
    #
    # The repeated attribute should be allowed: the function is not a target.
    if env.step(
        env.write_file("repeated.jaz", REPEATED_SOURCE),
        env.parse_module("repeated.jaz"),
    ):
        assert env.target_names() == ["build"]

    # We have an attribute list with a misspelled attribute. We load the file.
    #
    # It should raise a ParseError that names the attribute and its line.
    if env.step(
        env.write_file("misspelled.jaz", MISSPELLED_SOURCE),
        env.parse_module_and_catch_error("misspelled.jaz"),
    ):
        assert isinstance(env.error, ParseError)
        assert "interactve" in str(env.error)
        assert env.error.line == 4

    # We have an attribute list with a trailing comma. We load the file.
    #
    # It should raise a ParseError with the line of the attribute.
    if env.step(
        env.write_file("trailing_comma.jaz", TRAILING_COMMA_SOURCE),
        env.parse_module_and_catch_error("trailing_comma.jaz"),
    ):
        assert isinstance(env.error, ParseError)
        assert env.error.line == 4

    # We have an attribute list with an empty item between two commas. We load the
    # file.
    #
    # It should raise a ParseError with the line of the attribute.
    if env.step(
        env.write_file("empty_item.jaz", EMPTY_ITEM_SOURCE),
        env.parse_module_and_catch_error("empty_item.jaz"),
    ):
        assert isinstance(env.error, ParseError)
        assert env.error.line == 4

    # We have an attribute list whose names are not separated by a comma. We load
    # the file.
    #
    # It should raise a ParseError with the line of the attribute.
    if env.step(
        env.write_file("missing_comma.jaz", MISSING_COMMA_SOURCE),
        env.parse_module_and_catch_error("missing_comma.jaz"),
    ):
        assert isinstance(env.error, ParseError)
        assert env.error.line == 4

    # We have a deploy function with the attribute list [interactive, interactive]
    # before a local function that builds. We run deploy.
    #
    # The local function should be interactive: the build output goes to the
    # console, and is not part of the result.
    if env.step(
        env.write_file("local_list.jaz", LOCAL_LIST_SOURCE),
        env.parse_module("local_list.jaz"),
        env.evaluate("🐭.deploy()"),
        env.read_printed(),
    ):
        assert "building the images" in env.printed.splitlines()
        assert env.output == "1.2.3"

    # We have the attribute list [interactive, private] before a local function. We
    # load the file.
    #
    # It should raise a ParseError that names private: a local function is never a
    # target.
    if env.step(
        env.write_file("local_private.jaz", LOCAL_PRIVATE_SOURCE),
        env.parse_module_and_catch_error("local_private.jaz"),
    ):
        assert isinstance(env.error, ParseError)
        assert "private" in str(env.error)

    # We have the attribute list [interactive,] before a local function. We load
    # the file.
    #
    # It should raise a ParseError with the line of the attribute.
    if env.step(
        env.write_file("local_trailing_comma.jaz", LOCAL_TRAILING_COMMA_SOURCE),
        env.parse_module_and_catch_error("local_trailing_comma.jaz"),
    ):
        assert isinstance(env.error, ParseError)
        assert env.error.line == 2

    # We have a function body with [interactive] followed by a shell line. We load
    # the file.
    #
    # It should raise a ParseError with the line of the attribute: an attribute
    # must precede a function.
    if env.step(
        env.write_file("body_attribute.jaz", BODY_ATTRIBUTE_SOURCE),
        env.parse_module_and_catch_error("body_attribute.jaz"),
    ):
        assert isinstance(env.error, ParseError)
        assert env.error.line == 2

    # We have a function body with the misspelled [interactve] followed by a shell
    # line. We load the file.
    #
    # It should raise a ParseError that names the attribute, instead of running
    # the line as a shell command.
    if env.step(
        env.write_file("body_misspelled.jaz", BODY_MISSPELLED_SOURCE),
        env.parse_module_and_catch_error("body_misspelled.jaz"),
    ):
        assert isinstance(env.error, ParseError)
        assert "interactve" in str(env.error)
        assert env.error.line == 2

    # We have [private] before an assignment at the top level. We load the file.
    #
    # It should raise a ParseError with the line of the attribute.
    if env.step(
        env.write_file("before_assignment.jaz", TOP_LEVEL_BEFORE_ASSIGNMENT_SOURCE),
        env.parse_module_and_catch_error("before_assignment.jaz"),
    ):
        assert isinstance(env.error, ParseError)
        assert env.error.line == 4

    # We have [private] as the last line of the file. We load the file.
    #
    # It should raise a ParseError with the line of the attribute.
    if env.step(
        env.write_file("at_end.jaz", TOP_LEVEL_AT_END_SOURCE),
        env.parse_module_and_catch_error("at_end.jaz"),
    ):
        assert isinstance(env.error, ParseError)
        assert env.error.line == 4

    # We have a function body with shell tests that start with "[ " or "[[ ", the
    # last of which is followed by a local function header. We run the function.
    #
    # The tests should run as ordinary shell commands, and the local function
    # should be captured as usual.
    if env.step(
        env.write_file("shell_tests.jaz", SHELL_TESTS_SOURCE),
        env.parse_module("shell_tests.jaz"),
        env.evaluate("🐭.check()"),
    ):
        assert env.output == "checked"


class Env(TestEnv):
    def __post_init__(self):
        super().__post_init__()
        self.other_output = None

    # Queries

    def target_names(self):
        return [function.name for function in get_targets(self.root_module)]
