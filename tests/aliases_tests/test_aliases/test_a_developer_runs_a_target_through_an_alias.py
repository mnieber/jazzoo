from aliases_tests.aliases_test_env import Context, TestEnv

ALIASES = """
[alias]
b = build
fb = fe.build mode=debug
"""


def create_env(context: Context):
    return Env(context)


def test_a_developer_runs_a_target_through_an_alias(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a project with the targets build and fe.build (both with
    # mode="release"), and we define the aliases b and fb in
    # ~/.config/jazzoo/config.
    if env.step(
        env.write_jazzoo(),
        env.write_aliases(ALIASES),
    ):
        pass

    # We run jaz b.
    #
    # There is no target b, so the alias should be expanded, and build should run
    # with its default mode.
    if env.step(
        env.run_jaz("b"),
    ):
        assert env.exit_code == 0
        assert env.output_lines() == ["build mode=release"]

    # We run jaz fb.
    #
    # The expansion names a target in an export layer, and presets mode=debug.
    if env.step(
        env.run_jaz("fb"),
    ):
        assert env.exit_code == 0
        assert env.output_lines() == ["fe.build mode=debug"]

    # We run jaz fb mode=release.
    #
    # The argument on the command line should win over the one of the expansion.
    if env.step(
        env.run_jaz("fb", "mode=release"),
    ):
        assert env.exit_code == 0
        assert env.output_lines() == ["fe.build mode=release"]

    # We run jaz b debug, with a positional argument after the alias.
    #
    # The argument should be passed to the first parameter of build.
    if env.step(
        env.run_jaz("b", "debug"),
    ):
        assert env.exit_code == 0
        assert env.output_lines() == ["build mode=debug"]


class Env(TestEnv):
    pass
