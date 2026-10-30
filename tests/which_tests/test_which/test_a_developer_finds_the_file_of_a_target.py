from which_tests.which_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_a_developer_finds_the_file_of_a_target(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the project shop, with the target build, the target deploy that
    # tools.jaz defines, and the layer fe from fe/fe.jaz.
    if env.step(
        env.write_jazzoo(),
    ):
        pass

    # We run jaz --which build.
    #
    # It should print the absolute path of the jazzoo file, and not run build.
    if env.step(
        env.run_jaz_cli("--which", "build"),
    ):
        assert env.exit_code == 0
        assert env.output_lines() == [env.path("shop/jazzoo")]

    # We run jaz --which deploy.
    #
    # The jazzoo file exports deploy, but tools.jaz defines it, so it should print
    # the path of tools.jaz.
    if env.step(
        env.run_jaz_cli("--which", "deploy"),
    ):
        assert env.exit_code == 0
        assert env.output_lines() == [env.path("shop/tools.jaz")]

    # We run jaz --which fe.build.
    #
    # It should print the path of the file of the layer fe.
    if env.step(
        env.run_jaz_cli("--which", "fe.build"),
    ):
        assert env.exit_code == 0
        assert env.output_lines() == [env.path("shop/fe/fe.jaz")]

    # We run jaz --which fe, which names the layer rather than a target.
    #
    # It should print the path of the file of the layer.
    if env.step(
        env.run_jaz_cli("--which", "fe"),
    ):
        assert env.exit_code == 0
        assert env.output_lines() == [env.path("shop/fe/fe.jaz")]

    # We run jaz build --which, with the option after the target.
    #
    # It should be the same as jaz --which build.
    if env.step(
        env.run_jaz_cli("build", "--which"),
    ):
        assert env.exit_code == 0
        assert env.output_lines() == [env.path("shop/jazzoo")]


class Env(TestEnv):
    pass
