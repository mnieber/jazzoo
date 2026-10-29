import sys
import typing as T

from commands_tests.commands_test_env import CTRL_C, CTRL_D, Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_jaz_run_confirm(context: Context):
    # Create the test environment
    env = create_env(context)

    # We switch on the confirmation of commands, run jaz-run in a terminal with a
    # command that creates a file, and answer n.
    #
    # The command should not run, and jaz-run should exit with 0, so that a shell
    # script continues.
    if env.step(
        env.set_env("JAZZOO_CONFIRM", "1"),
        env.run_jaz_run_in_pty("-c", "touch ran.txt", answers=["n"]),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.prompts == [f"({env.path('')}) touch ran.txt"]
        assert not env.file_exists("ran.txt")

    # We run the same command, and answer q.
    #
    # jaz-run should exit with 130, as after a ctrl-c, and say that the user
    # aborted.
    if env.step(
        env.run_jaz_run_in_pty("-c", "touch ran.txt", answers=["q"]),
    ):
        assert env.exit_code == 130
        assert env.pty_lines() == ["jaz-run: aborted by the user"]
        assert not env.file_exists("ran.txt")

    # We run the same command, and press ctrl-d at the prompt.
    #
    # The end of input should abort, as q does.
    if env.step(
        env.run_jaz_run_in_pty("-c", "touch ran.txt", answers=[CTRL_D]),
    ):
        assert env.exit_code == 130
        assert env.pty_lines() == ["jaz-run: aborted by the user"]
        assert not env.file_exists("ran.txt")

    # We run the same command, and press ctrl-c at the prompt.
    #
    # jaz-run should exit with 130, without the message of an abort.
    if env.step(
        env.run_jaz_run_in_pty("-c", "touch ran.txt", answers=[CTRL_C]),
    ):
        assert env.exit_code == 130
        assert "aborted by the user" not in env.pty_output
        assert not env.file_exists("ran.txt")

    # We run jaz-run with --echo, and answer y.
    #
    # The prompt should replace the echo: only the output of the command is
    # printed.
    if env.step(
        env.run_jaz_run_in_pty("--echo", "-c", "echo hi", answers=["y"]),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.prompts == [f"({env.path('')}) echo hi"]
        assert env.pty_lines() == ["hi"]


class Env(TestEnv):
    def run_jaz_run_in_pty(self, *args: str, answers: T.Sequence[str]):
        self._run_in_pty(
            [sys.executable, "-m", "jazzoo.commands", *args], answers=answers
        )
