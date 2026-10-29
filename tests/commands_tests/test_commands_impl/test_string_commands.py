from commands_tests.commands_test_env import Context, TestEnv

from jazzoo.commands import CommandFailedError, CommandNotFoundError


def create_env(context: Context):
    return Env(context)


def test_string_commands(context: Context):
    # Create the test environment
    env = create_env(context)

    # We run a string command that uses &&, ; and a pipe whose output is redirected
    # to a file.
    #
    # It should have run in bash: the first two commands print to the console, and
    # the file holds the output of the pipe.
    if env.step(
        env.run("echo a && echo b; echo c | tr c C > out.txt", cwd=env.path("")),
        env.read_printed(),
    ):
        assert env.printed == "a\nb\n"
        assert env.read_file("out.txt") == "C\n"

    # We run a string command that uses an environment variable and ~.
    #
    # Both should be expanded by bash.
    if env.step(
        env.set_env("GREETING", "hello"),
        env.set_env("HOME", env.path("home")),
        env.run("echo $GREETING ~", capture=True),
    ):
        assert env.result.stdout == f"hello {env.path('home')}\n"

    # We have two text files, and run a string command with a glob in their
    # directory.
    #
    # The glob should match both files.
    if env.step(
        env.write_file("docs/a.txt", ""),
        env.write_file("docs/b.txt", ""),
        env.run("echo *.txt", cwd=env.path("docs"), capture=True),
    ):
        assert env.result.stdout == "a.txt b.txt\n"

    # We run a string command with single quotes.
    #
    # The quoting should work as in bash.
    if env.step(
        env.run("printf '%s\\n' 'a b'", capture=True),
    ):
        assert env.result.stdout == "a b\n"

    # We run a string command whose executable does not exist.
    #
    # Bash reports it with exit code 127, so it should raise a CommandFailedError,
    # not a CommandNotFoundError.
    if env.step(
        env.run_and_catch_error("no-such-tool-for-jazzoo-tests --help", capture=True),
    ):
        assert isinstance(env.error, CommandFailedError)
        assert not isinstance(env.error, CommandNotFoundError)
        assert env.error.result.returncode == 127

    # We run an empty string command, and one with only whitespace.
    #
    # Both should raise a ValueError.
    if env.step(
        env.run_and_catch_error(""),
        env.run_and_catch_error("   ", store_as="other_error"),
    ):
        assert isinstance(env.error, ValueError)
        assert isinstance(env.other_error, ValueError)


class Env(TestEnv):
    def __post_init__(self):
        super().__post_init__()
        self.other_error = None
