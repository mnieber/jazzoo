import json
import os
import sys

from commands_tests.commands_test_env import Context, TestEnv

from jazzoo.commands import CommandNotFoundError

PRINT_ARGS = "import json, sys; print(json.dumps(sys.argv[1:]))"

HELLO_TOOL = """
#!/bin/sh
echo "hello from the tool"
"""


def create_env(context: Context):
    return Env(context)


def test_list_commands(context: Context):
    # Create the test environment
    env = create_env(context)

    # We run a list command whose arguments look like shell syntax.
    #
    # They should arrive unchanged: a list command does not run in a shell.
    if env.step(
        env.set_env("HOME", env.path("home")),
        env.run(
            [sys.executable, "-c", PRINT_ARGS, "$HOME", "*", "|", "a b"],
            capture=True,
        ),
    ):
        assert json.loads(env.result.stdout) == ["$HOME", "*", "|", "a b"]

    # We run a list command whose executable is not on the PATH.
    #
    # It should raise a CommandNotFoundError that names the executable.
    if env.step(
        env.run_and_catch_error(["no-such-tool-for-jazzoo-tests", "--help"]),
    ):
        assert isinstance(env.error, CommandNotFoundError)
        assert "no-such-tool-for-jazzoo-tests" in str(env.error)

    # We have an executable in a bin dir that is not on the PATH, and run it by
    # name.
    #
    # It should not be found.
    if env.step(
        env.write_executable("bin/hello-tool", HELLO_TOOL),
        env.run_and_catch_error(["hello-tool"]),
    ):
        assert isinstance(env.error, CommandNotFoundError)

    # We run it again, with the bin dir on the PATH of env.
    #
    # The PATH lookup should use the PATH of env, and find the tool.
    if env.step(
        env.run(
            ["hello-tool"],
            env={"PATH": env.path("bin") + os.pathsep + os.environ["PATH"]},
            capture=True,
        ),
    ):
        assert env.result.stdout == "hello from the tool\n"

    # We run the tool by its path.
    #
    # A first term that contains a slash should be used as a path.
    if env.step(
        env.run([env.path("bin/hello-tool")], capture=True),
    ):
        assert env.result.stdout == "hello from the tool\n"

    # We run an empty list command.
    #
    # It should raise a ValueError.
    if env.step(
        env.run_and_catch_error([]),
    ):
        assert isinstance(env.error, ValueError)


class Env(TestEnv):
    pass
