from aliases_tests.aliases_test_env import SHOP_JAZZOO, Context, TestEnv

from jazzoo import JazzooError

ALIASES = """
[alias]
b = build
bb = b
x = nope
Bd = build mode=debug
"""

# The shop project, with an extra target named like the alias b
JAZZOO_WITH_B = (
    SHOP_JAZZOO
    + """
b():
    @echo "target b"
"""
)


def create_env(context: Context):
    return Env(context)


def test_alias_lookup(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a project with a target b, and an alias b = build.
    if env.step(
        env.write_jazzoo(JAZZOO_WITH_B),
        env.write_aliases(ALIASES),
    ):
        pass

    # We run jaz b.
    #
    # The target should win over the alias, silently.
    if env.step(
        env.run_jaz_cli("b"),
    ):
        assert env.exit_code == 0
        assert env.output_lines() == ["target b"]
        assert env.printed_err == ""

    # We remove the target b, and run jaz bb, whose expansion is the alias b.
    #
    # Aliases are not chained, so this should be an error that names the target
    # and the alias.
    if env.step(
        env.write_jazzoo(),
        env.run_jaz_and_catch_error("bb"),
    ):
        assert isinstance(env.error, JazzooError)
        assert env.error.message == 'no such target: b (the expansion of alias "bb")'

    # We run jaz x as the console script does; the target of its expansion does
    # not exist.
    #
    # jaz should print the error that names the target and the alias, and exit
    # with 1.
    if env.step(
        env.run_jaz_cli("x"),
    ):
        assert env.exit_code == 1
        assert env.printed_err == (
            'jazzoo: error: no such target: nope (the expansion of alias "x")\n'
        )

    # We run jaz nope, which is neither a target nor an alias.
    #
    # This should be the usual error.
    if env.step(
        env.run_jaz_and_catch_error("nope"),
    ):
        assert isinstance(env.error, JazzooError)
        assert env.error.message == "no such target: nope"

    # We run jaz bd and jaz Bd; only the alias Bd exists.
    #
    # Alias names are case-sensitive.
    if env.step(
        env.run_jaz_and_catch_error("bd"),
    ):
        assert isinstance(env.error, JazzooError)
        assert env.error.message == "no such target: bd"

    if env.step(
        env.run_jaz("Bd"),
    ):
        assert env.output_lines() == ["build mode=debug"]

    # We run jaz --list b.
    #
    # Listing describes the jazzoo file, so the alias should not be expanded.
    if env.step(
        env.run_jaz_and_catch_error("--list", "b"),
    ):
        assert isinstance(env.error, JazzooError)
        assert env.error.message == "no such target: b"

    # We run jaz --list-all.
    #
    # The listing should not show the aliases.
    if env.step(
        env.run_jaz("--list-all"),
    ):
        assert env.output_lines() == ["build", "greet", "fe.build"]

    # We run jaz build b, with the name of an alias as an argument.
    #
    # Only the target can be an alias, so b should be passed as it is.
    if env.step(
        env.run_jaz("build", "b"),
    ):
        assert env.output_lines() == ["build mode=b"]


class Env(TestEnv):
    pass
