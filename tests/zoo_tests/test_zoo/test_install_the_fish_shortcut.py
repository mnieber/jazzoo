from zoo_tests.zoo_test_env import FISH_FILES, FISH_MANAGED_LINE, Context, TestEnv

# functions/zz.fish as an older version of jazzoo might have written it
OLD_ZZ = f"""
{FISH_MANAGED_LINE}
function zz --description "an older version"
end
"""


def create_env(context: Context):
    return Env(context)


def test_install_the_fish_shortcut(context: Context):
    # Create the test environment
    env = create_env(context)

    # We run `zoo env --install-fish`.
    #
    # It should write the zz function, the completions of zz, jaz, jazzoo and
    # zoo, and the startup file to ~/.config/fish, each starting with the
    # managed line. It should name the
    # files and remind us to open a new shell on stderr, and print nothing on
    # stdout, which is for lines to source.
    if env.step(
        env.run_zoo("env", "--install-fish"),
    ):
        assert env.exit_code == 0
        assert env.output == ""
        for name in FISH_FILES:
            assert env.read_lines(env.fish_file(name))[0] == FISH_MANAGED_LINE
            assert env.fish_file(name) in env.printed_err
        assert "Open a new fish shell" in env.printed_err

    # We look at the startup file.
    #
    # It should source latest.fish of the zoo registry, by its absolute path.
    if env.step():
        assert env.config_dir() + "/latest.fish" in env.read_file(
            env.fish_file("conf.d/zoo.fish")
        )

    # The zz function was written by an older version of jazzoo. We run the
    # installer again.
    #
    # The installer wrote the old file itself, so it should write it again.
    if env.step(
        env.write_file(env.fish_file("functions/zz.fish"), OLD_ZZ),
        env.run_zoo("env", "--install-fish"),
    ):
        assert env.exit_code == 0
        assert "an older version" not in env.read_file(
            env.fish_file("functions/zz.fish")
        )
        assert "function zz" in env.read_file(env.fish_file("functions/zz.fish"))


class Env(TestEnv):
    pass
