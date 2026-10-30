from completions_tests.completions_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_a_developer_completes_a_jaz_command(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the project shop with the targets build and deploy, the layers fe
    # and db, and the aliases b, fb and dep.
    if env.step(
        env.write_jazzoo(),
        env.write_aliases(),
        env.make_dir("shop/src"),
    ):
        pass

    # We type `jaz ` and press tab.
    #
    # It should offer the targets, the layers as `fe.` and `db.`, and the aliases,
    # but not the private function. A target should have its signature as
    # description, and a layer should have `layer`.
    if env.step(
        env.complete_jaz(""),
    ):
        assert env.exit_code == 0
        assert sorted(env.candidates()) == [
            "b",
            "build",
            "db.",
            "dep",
            "deploy",
            "fb",
            "fe.",
        ]
        assert env.descriptions()["build"] == 'build(mode="debug", watch="no")'
        assert env.descriptions()["fe."] == "layer"

    # We type `jaz fe.` and press tab.
    #
    # It should offer the members of the layer fe, with the nested layer lint as
    # `fe.lint.`.
    if env.step(
        env.complete_jaz("fe."),
    ):
        assert sorted(env.candidates()) == ["fe.build", "fe.lint.", "fe.test"]
        assert env.descriptions()["fe.build"] == 'fe.build(mode="release")'

    # We type `jaz fe.lint.` and press tab.
    #
    # It should offer the members of the nested layer.
    if env.step(
        env.complete_jaz("fe.lint."),
    ):
        assert sorted(env.candidates()) == ["fe.lint.check", "fe.lint.fix"]

    # We choose build, and press tab for its arguments.
    #
    # It should offer the parameters of build.
    if env.step(
        env.complete_jaz("build", ""),
    ):
        assert sorted(env.candidates()) == ["mode=", "watch="]

    # We give the argument mode, and press tab again.
    #
    # It should only offer the parameter that is not given yet.
    if env.step(
        env.complete_jaz("build", "mode=release", ""),
    ):
        assert env.candidates() == ["watch="]

    # We type `jaz build mode=` and press tab.
    #
    # It should offer the files of the current directory as values, and a
    # directory should end in a slash.
    if env.step(
        env.complete_jaz("build", "mode="),
    ):
        assert sorted(env.candidates()) == [
            "mode=db.jaz",
            "mode=fe.jaz",
            "mode=jazzoo",
            "mode=lint.jaz",
            "mode=src/",
        ]

    # We type `jaz --` and press tab.
    #
    # It should offer the options of jaz.
    if env.step(
        env.complete_jaz("--"),
    ):
        assert sorted(env.candidates()) == [
            "--confirm",
            "--file",
            "--help",
            "--list",
            "--list-all",
            "--trace",
            "--which",
        ]


class Env(TestEnv):
    pass
