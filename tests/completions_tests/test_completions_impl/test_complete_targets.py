from completions_tests.completions_test_env import Context, TestEnv

OTHER_JAZ = """
hello(name):
    @echo "hello 🐆.name"
"""


def create_env(context: Context):
    return Env(context)


def test_complete_targets(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the project shop, its aliases, and a second jazzoo file other.jaz.
    if env.step(
        env.write_jazzoo(),
        env.write_aliases(),
        env.write_file("shop/other.jaz", OTHER_JAZ),
    ):
        pass

    # We complete `jaz b`.
    #
    # Only the candidates that start with b should be printed: the target build
    # and the alias b, not deploy.
    if env.step(
        env.complete_jaz("b"),
    ):
        assert sorted(env.candidates()) == ["b", "build"]

    # We complete `jaz `, and look at the order of the candidates.
    #
    # It should be the order of `jaz --list`: the targets, then the layers, then
    # the aliases in the order of the config file. The alias build has the name
    # of a target, so it should be left out.
    if env.step(
        env.complete_jaz(""),
    ):
        assert env.candidates() == [
            "build",
            "deploy",
            "fe.",
            "db.",
            "b",
            "fb",
            "dep",
        ]

    # We complete a path in a layer that does not exist.
    #
    # It should offer nothing, and print no error.
    if env.step(
        env.complete_jaz("nope."),
    ):
        assert env.exit_code == 0
        assert env.output == ""
        assert env.printed_err == ""

    # We complete the target after some options of jaz.
    #
    # The options should be skipped, and the targets offered.
    if env.step(
        env.complete_jaz("--trace", "--confirm", "de"),
    ):
        assert sorted(env.candidates()) == ["dep", "deploy"]

    # We complete the target after `--file other.jaz`.
    #
    # It should offer the targets of other.jaz instead of those of the jazzoo
    # file, and still the aliases.
    if env.step(
        env.complete_jaz("--file", "other.jaz", "h"),
    ):
        assert env.candidates() == ["hello"]

    # We complete the arguments of hello, with `--file other.jaz` after the
    # target.
    #
    # The parameters should be those of hello in other.jaz.
    if env.step(
        env.complete_jaz("hello", "--file", "other.jaz", ""),
    ):
        assert env.candidates() == ["name="]


class Env(TestEnv):
    pass
