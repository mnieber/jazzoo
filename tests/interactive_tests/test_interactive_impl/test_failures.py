from interactive_tests.interactive_test_env import Context, TestEnv

from jazzoo import ExecutionError

JAZZOO_SOURCE = """
[interactive]
migrate():
    @printf 'database is %s\\n' locked >&2; exit 3
"""


def create_env(context: Context):
    return Env(context)


def test_failures(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have an interactive function whose shell line writes an error to stderr
    # and exits with 3. We run it.
    #
    # It should raise an ExecutionError that names the exit code and says that the
    # command failed. The error message on stderr should have been printed to the
    # console, not captured into the ExecutionError.
    if env.step(
        env.write_file("migrate.jaz", JAZZOO_SOURCE),
        env.parse_module("migrate.jaz"),
        env.evaluate_and_catch_error("🐭.migrate()"),
        env.read_printed(),
    ):
        assert isinstance(env.error, ExecutionError)
        assert "exit code 3" in str(env.error)
        assert "command failed" in str(env.error)
        assert "database is locked" not in str(env.error)
        assert env.printed_err == "database is locked\n"


class Env(TestEnv):
    pass
