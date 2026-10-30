from completions_tests.completions_test_env import Context, TestEnv

# A jazzoo file with a line outside a function that is not a statement
BROKEN_JAZZOO = """
build():
    @echo "build"

this is not jazzoo
"""


def create_env(context: Context):
    return Env(context)


def test_complete_errors(context: Context):
    # Create the test environment
    env = create_env(context)

    # We are in a directory without a jazzoo file, and complete `jaz `.
    #
    # Fish shows what is printed in the command line of the developer, so it
    # should print nothing, also not on stderr, and exit with 0.
    if env.step(
        env.make_dir("empty"),
        env.change_dir("empty"),
        env.complete_jaz(""),
    ):
        assert env.exit_code == 0
        assert env.output == ""
        assert env.printed_err == ""

    # We have a jazzoo file that does not parse, and complete `jaz `.
    #
    # It should print nothing, and exit with 0.
    if env.step(
        env.write_file("broken/jazzoo", BROKEN_JAZZOO),
        env.change_dir("broken"),
        env.complete_jaz(""),
    ):
        assert env.exit_code == 0
        assert env.output == ""
        assert env.printed_err == ""

    # We have the project shop and an alias config file that is not valid INI,
    # and complete `jaz `.
    #
    # The aliases should be left out, and the targets still offered, without an
    # error.
    if env.step(
        env.write_jazzoo(),
        env.write_aliases("b = build\n"),
        env.complete_jaz(""),
    ):
        assert env.exit_code == 0
        assert sorted(env.candidates()) == ["build", "db.", "deploy", "fe."]
        assert env.printed_err == ""

    # We complete a command line that is not valid for jaz: an unknown option,
    # and a --file that does not exist.
    #
    # Neither should fail: the unknown option is skipped, and the missing file
    # offers no targets.
    if env.step(
        env.complete_jaz("--frobnicate", "de"),
    ):
        assert env.exit_code == 0
        assert env.candidates() == ["deploy"]
        assert env.printed_err == ""

    if env.step(
        env.complete_jaz("--file", "missing.jaz", ""),
    ):
        assert env.exit_code == 0
        assert env.output == ""
        assert env.printed_err == ""

    # We run `jaz --complete build`, without `--`.
    #
    # This should be a usage error with exit code 2.
    if env.step(
        env.run_jaz_and_catch_exit("--complete", "build"),
    ):
        assert env.system_exit is not None
        assert env.system_exit.code == 2

    # We run `jaz --help`.
    #
    # --complete is only for the fish files, so the usage should not mention it.
    if env.step(
        env.run_jaz("--help"),
    ):
        assert env.exit_code == 0
        assert "--complete" not in env.output


class Env(TestEnv):
    pass
