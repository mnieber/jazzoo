from aliases_tests.aliases_test_env import Context, TestEnv

from jazzoo import ArgumentError

ALIASES = """
[alias]
bd = build debug
gj = greet jane
gn = greet name=jane
hi = greet greeting=hi
gd = greet "name=jane doe"
pct = greet name=100%
g = greet
twice = greet jane name=joe
"""


def create_env(context: Context):
    return Env(context)


def test_alias_arguments(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a project with the targets build(mode="release") and
    # greet(name, greeting="hello"), and aliases that preset their arguments.
    if env.step(
        env.write_jazzoo(),
        env.write_aliases(ALIASES),
    ):
        pass

    # We run jaz bd, whose expansion has a positional argument.
    #
    # The argument should be passed to the first parameter.
    if env.step(
        env.run_jaz("bd"),
    ):
        assert env.output_lines() == ["build mode=debug"]

    # We run jaz bd test.
    #
    # The positional argument on the command line should override the positional
    # argument of the expansion.
    if env.step(
        env.run_jaz("bd", "test"),
    ):
        assert env.output_lines() == ["build mode=test"]

    # We run jaz gn joe; the expansion names the first parameter, the command line
    # gives it positionally.
    #
    # Both are the same parameter, so the command line should win, without an
    # error.
    if env.step(
        env.run_jaz("gn", "joe"),
    ):
        assert env.output_lines() == ["greet name=joe greeting=hello"]

    # We run jaz gj name=joe; the expansion gives the first parameter
    # positionally, the command line names it.
    #
    # The command line should win, without an error.
    if env.step(
        env.run_jaz("gj", "name=joe"),
    ):
        assert env.output_lines() == ["greet name=joe greeting=hello"]

    # We run jaz gj greeting=hey, which names another parameter than the
    # expansion.
    #
    # The argument of the expansion should be kept.
    if env.step(
        env.run_jaz("gj", "greeting=hey"),
    ):
        assert env.output_lines() == ["greet name=jane greeting=hey"]

    # We run jaz hi jane, and jaz hi jane greeting=hey.
    #
    # The positional argument may follow the arguments of the expansion, and a
    # named argument on the command line overrides the one of the expansion.
    if env.step(
        env.run_jaz("hi", "jane"),
    ):
        assert env.output_lines() == ["greet name=jane greeting=hi"]

    if env.step(
        env.run_jaz("hi", "jane", "greeting=hey"),
    ):
        assert env.output_lines() == ["greet name=jane greeting=hey"]

    # We run jaz gd, whose expansion quotes an argument with a space.
    #
    # The quoted argument should arrive as one value.
    if env.step(
        env.run_jaz("gd"),
    ):
        assert env.output_lines() == ["greet name=jane doe greeting=hello"]

    # We run jaz pct, whose expansion contains a %.
    #
    # There is no interpolation, so the % should be taken as it is.
    if env.step(
        env.run_jaz("pct"),
    ):
        assert env.output_lines() == ["greet name=100% greeting=hello"]

    # We run jaz twice, whose expansion names a parameter both positionally and by
    # name.
    #
    # Within the expansion the usual rules hold, so this should be an
    # ArgumentError.
    if env.step(
        env.run_jaz_and_catch_error("twice"),
    ):
        assert isinstance(env.error, ArgumentError)
        assert "name" in env.error.message

    # We run jaz g jane name=joe, which names a parameter both positionally and by
    # name on the command line.
    #
    # Within the command line the usual rules hold, so this should be an
    # ArgumentError.
    if env.step(
        env.run_jaz_and_catch_error("g", "jane", "name=joe"),
    ):
        assert isinstance(env.error, ArgumentError)
        assert "name" in env.error.message


class Env(TestEnv):
    pass
