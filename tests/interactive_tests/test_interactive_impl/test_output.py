import sys

from interactive_tests.interactive_test_env import Context, TestEnv

REPORT_SOURCE = f"""
[interactive]
report():
    @echo "from the shell"
    @echo "shell warning" >&2

    #!{sys.executable}
    import sys

    print("from python")
    print("python warning", file=sys.stderr)
"""

RETURN_VALUES_SOURCE = """
[interactive]
show-stdout():
    @echo "hello"
    🐆.retval = ⚙️.stdout

[interactive]
greet():
    @echo "hello"

[interactive]
greet-and-tell():
    @echo "hello"
    🐆.retval = "done"
"""

ASK_SOURCE = """
[interactive]
ask():
    #!/usr/bin/env bash
    read name
    echo "hello $name"
"""

CALLEES_SOURCE = """
[private]
_version():
    @echo "1.2.3"

[private]
[interactive]
_live():
    @echo "live"

[interactive]
get-version():
    🐆.retval = 🐭._version()

[interactive]
get-live():
    🐆.retval = 🐭._live()
"""


def create_env(context: Context):
    return Env(context)


def test_output(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have an interactive function with shell lines and a Python block that
    # write to stdout and stderr. We run it.
    #
    # Their output should appear on the console.
    if env.step(
        env.write_file("report.jaz", REPORT_SOURCE),
        env.parse_module("report.jaz"),
        env.evaluate("🐭.report()"),
        env.read_printed(),
    ):
        assert env.printed == "from the shell\nfrom python\n"
        assert env.printed_err == "shell warning\npython warning\n"

    # We have an interactive function that prints, and then returns ⚙️.stdout.
    #
    # ⚙️.stdout should be empty: jazzoo does not see the output.
    if env.step(
        env.write_file("return_values.jaz", RETURN_VALUES_SOURCE),
        env.parse_module("return_values.jaz"),
        env.evaluate("🐭.show-stdout()"),
    ):
        assert env.output == ""

    # We run an interactive function that prints, and returns nothing explicitly.
    #
    # Its default return value should be empty.
    if env.step(
        env.evaluate("🐭.greet()"),
    ):
        assert env.output == ""

    # We run an interactive function that sets 🐆.retval.
    #
    # It should return that value.
    if env.step(
        env.evaluate("🐭.greet-and-tell()"),
    ):
        assert env.output == "done"

    # We have an interactive function that reads a name from stdin. We run jaz, and
    # feed it a name.
    #
    # The block should read the stdin of jaz.
    if env.step(
        env.write_file("jazzoo", ASK_SOURCE),
        env.run_jaz("ask", input="jane\n"),
    ):
        assert env.exit_code == 0, env.printed_err
        assert env.output == "hello jane\n"

    # We have an interactive function that returns the value of a captured
    # function.
    #
    # The captured function should be captured as usual: the attribute is not
    # inherited.
    if env.step(
        env.write_file("callees.jaz", CALLEES_SOURCE),
        env.parse_module("callees.jaz"),
        env.evaluate("🐭.get-version()"),
    ):
        assert env.output == "1.2.3"

    # We run an interactive function that returns the value of an interactive
    # function.
    #
    # The value should be empty, because the callee is interactive itself.
    if env.step(
        env.evaluate("🐭.get-live()"),
    ):
        assert env.output == ""


class Env(TestEnv):
    pass
