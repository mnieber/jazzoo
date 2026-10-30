import os

from zoo_tests.zoo_test_env import FISH_MANAGED_LINE, Context, TestEnv

from jazzoo.zoo.errors import FishFileExistsError

# Files of the developer, with the names of files that the installer writes
OWN_ZZ = """
function zz
    echo "my own zz"
end
"""

OWN_STARTUP = """
set -gx EDITOR vim
"""

OWN_JAZ_COMPLETIONS = """
# my own completions
complete -c jaz -f -a "build deploy"
"""

MANAGED_ZZ = f"""
{FISH_MANAGED_LINE}
function zz
end
"""


def create_env(context: Context):
    return Env(context)


def test_install_fish_errors(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have our own functions/zz.fish and conf.d/zoo.fish, and run the
    # installer.
    #
    # It should raise a FishFileExistsError that names both files, and write
    # nothing: our files are unchanged, and the completions are not written.
    if env.step(
        env.write_file(env.fish_file("functions/zz.fish"), OWN_ZZ),
        env.write_file(env.fish_file("conf.d/zoo.fish"), OWN_STARTUP),
        env.run_zoo_and_catch_error("env", "--install-fish"),
    ):
        assert isinstance(env.error, FishFileExistsError)
        assert env.fish_file("functions/zz.fish") in str(env.error)
        assert env.fish_file("conf.d/zoo.fish") in str(env.error)
        assert "my own zz" in env.read_file(env.fish_file("functions/zz.fish"))
        assert "EDITOR" in env.read_file(env.fish_file("conf.d/zoo.fish"))
        assert not env.exists(env.fish_file("completions/zz.fish"))

    # We run the installer as the console script.
    #
    # It should print the error with both files, and exit with 1.
    if env.step(
        env.run_zoo_cli("env", "--install-fish"),
    ):
        assert env.exit_code == 1
        assert env.fish_file("functions/zz.fish") in env.printed_err
        assert env.fish_file("conf.d/zoo.fish") in env.printed_err

    # We give functions/zz.fish the managed line, remove our conf.d/zoo.fish,
    # and run the installer again.
    #
    # A file with the managed line is not in the way, so the installer should
    # write all files.
    if env.step(
        env.write_file(env.fish_file("functions/zz.fish"), MANAGED_ZZ),
        env.remove_file(env.fish_file("conf.d/zoo.fish")),
        env.run_zoo("env", "--install-fish"),
    ):
        assert env.exit_code == 0
        assert env.exists(env.fish_file("completions/zz.fish"))
        assert env.read_lines(env.fish_file("conf.d/zoo.fish"))[0] == (
            FISH_MANAGED_LINE
        )

    # We replace completions/jaz.fish with our own, and run the installer again.
    #
    # The completions of jaz are in the way, so it should raise a
    # FishFileExistsError that names the file, and leave our file unchanged.
    if env.step(
        env.write_file(env.fish_file("completions/jaz.fish"), OWN_JAZ_COMPLETIONS),
        env.run_zoo_and_catch_error("env", "--install-fish"),
    ):
        assert isinstance(env.error, FishFileExistsError)
        assert env.fish_file("completions/jaz.fish") in str(env.error)
        assert "my own completions" in env.read_file(
            env.fish_file("completions/jaz.fish")
        )


class Env(TestEnv):
    def remove_file(self, path: str):
        os.remove(path)
