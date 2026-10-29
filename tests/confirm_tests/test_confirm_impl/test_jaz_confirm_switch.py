import os
import sys

from confirm_tests.confirm_test_env import Context, TestEnv

# The module-level assignment calls _mark, which leaves a file when the module is
# loaded
JAZZOO_SOURCE = f"""
[private]
_mark():
    @touch loaded.txt

🐭.marker = 🐭._mark()

deploy(env="staging"):
    #!{sys.executable}
    from jazzoo.commands import run

    run("echo deployed 🐆.env")
"""


def create_env(context: Context):
    return Env(context)


def test_jaz_confirm_switch(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a jazzoo file with a deploy target that runs a command for an
    # environment (staging by default). We set
    # JAZZOO_CONFIRM to 0, and run jaz --confirm deploy in a terminal.
    #
    # jaz --confirm should overwrite the variable, so the command should be
    # confirmed.
    if env.step(
        env.write_file("jazzoo", JAZZOO_SOURCE),
        env.set_env("JAZZOO_CONFIRM", "0"),
        env.run_jaz_in_pty("--confirm", "deploy", answers=["y"]),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.prompts == [f"({env.path('')}) echo deployed staging"]
        assert env.pty_lines() == ["deployed staging"]

    # We run jaz deploy --confirm env=prod, with the option between the target and
    # its argument.
    #
    # The options of jaz may appear anywhere, so the command should be confirmed,
    # and env=prod should be the argument of the target.
    if env.step(
        env.run_jaz_in_pty("deploy", "--confirm", "env=prod", answers=["y"]),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.prompts == [f"({env.path('')}) echo deployed prod"]
        assert env.pty_lines() == ["deployed prod"]

    # We run jaz deploy prod --confirm, with a positional argument and the option
    # at the end.
    #
    # The command should be confirmed, and prod should be the argument of the
    # target.
    if env.step(
        env.run_jaz_in_pty("deploy", "prod", "--confirm", answers=["y"]),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.prompts == [f"({env.path('')}) echo deployed prod"]
        assert env.pty_lines() == ["deployed prod"]

    # We remove the file that loading the module leaves, and run jaz --confirm
    # deploy without a controlling terminal.
    #
    # jaz should fail with a message that a terminal is needed. It fails before it
    # loads the root module, so the module-level assignment should not have run.
    if env.step(
        env.remove_file("loaded.txt"),
        env.run_jaz_without_terminal("--confirm", "deploy"),
    ):
        assert env.exit_code != 0
        assert "--confirm needs a terminal" in env.printed_err
        assert "deployed" not in env.output
        assert not env.file_exists("loaded.txt")

    # We run jaz --confirm --list without a controlling terminal.
    #
    # No target runs, so --confirm should be ignored, and the targets should be
    # listed.
    if env.step(
        env.run_jaz_without_terminal("--confirm", "--list"),
    ):
        assert env.exit_code == 0, env.printed_err
        assert "deploy" in env.output

    # We run jaz --confirm --help without a controlling terminal.
    #
    # --confirm should be ignored, and the usage printed.
    if env.step(
        env.run_jaz_without_terminal("--confirm", "--help"),
    ):
        assert env.exit_code == 0, env.printed_err
        assert "usage" in env.output


class Env(TestEnv):
    def remove_file(self, name: str):
        os.remove(self.path(name))
