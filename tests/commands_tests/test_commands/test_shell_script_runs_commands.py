import shlex
import sys

from commands_tests.commands_test_env import Context, TestEnv

# Runs jaz-run without depending on an installed console script
JAZ_RUN = f"{shlex.quote(sys.executable)} -m jazzoo.commands"

SCRIPT = f"""
set -e

{JAZ_RUN} echo "two words"
{JAZ_RUN} -c "touch migrated.txt"
version=$({JAZ_RUN} -c "echo v1")
echo "version=$version"
"""


def create_env(context: Context):
    return Env(context)


def test_shell_script_runs_commands(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a bash script that uses jaz-run for a list command, for a string
    # command, and for a string command whose output it captures. We switch on the
    # confirmation of commands, and run the script in a terminal. We answer y, n
    # and y.
    #
    # Each command should be confirmed, also the captured one, whose prompt still
    # reaches the terminal. The list command should have received "two words" as
    # one argument. The skipped command should not have run, and the script should
    # have continued (jaz-run exits with 0 for a skipped command). The captured
    # output should be returned to the script.
    if env.step(
        env.write_file("deploy.sh", SCRIPT),
        env.set_env("JAZZOO_CONFIRM", "1"),
        env.run_bash_script_in_pty("deploy.sh", answers=["y", "n", "y"]),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.prompts == [
            f"({env.path('')}) echo 'two words'",
            f"({env.path('')}) touch migrated.txt",
            f"({env.path('')}) echo v1",
        ]
        assert not env.file_exists("migrated.txt")
        assert env.pty_lines() == ["two words", "version=v1"]


class Env(TestEnv):
    def run_bash_script_in_pty(self, name: str, answers):
        self._run_in_pty(["bash", self.path(name)], answers=answers)
