import sys

from confirm_tests.confirm_test_env import Context, TestEnv

JAZZOO_SOURCE = f"""
deploy():
    @echo start
    @jaz-run -c "echo built"
    #!{sys.executable}
    from jazzoo.commands import run

    result = run("touch migrated.txt")
    print("migrate skipped=" + str(result.skipped), flush=True)
    run("echo deployed")

    #!
    @echo done
"""


def create_env(context: Context):
    return Env(context)


def test_jaz_confirms_commands(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a jazzoo file with a deploy target. It has a shell line, a shell line
    # that runs a command with jaz-run, and a Python block that runs two commands
    # with run. We run jaz --confirm deploy in a terminal, and answer y, n and q.
    #
    # The plain shell line should run without a prompt. The jaz-run command and the
    # commands of the Python block should be confirmed. The jaz-run command should
    # have run, the first command of the block should have been skipped, and q
    # should have aborted the block. The block fails, so jaz should stop the run
    # with a non-zero exit code, and the last line of the target never runs.
    if env.step(
        env.write_file("jazzoo", JAZZOO_SOURCE),
        env.run_jaz_in_pty("--confirm", "deploy", answers=["y", "n", "q"]),
    ):
        assert env.prompts == [
            f"({env.path('')}) echo built",
            f"({env.path('')}) touch migrated.txt",
            f"({env.path('')}) echo deployed",
        ]
        assert env.exit_code != 0
        assert env.pty_lines()[:2] == ["start", "built"]
        assert not env.file_exists("migrated.txt")
        assert "deployed" not in env.pty_lines()
        assert "done" not in env.pty_lines()

    # We run jaz deploy, without --confirm.
    #
    # Every line should run without a prompt.
    if env.step(
        env.run_jaz_in_pty("deploy"),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.prompts == []
        assert env.pty_lines() == [
            "start",
            "built",
            "migrate skipped=False",
            "deployed",
            "done",
        ]
        assert env.file_exists("migrated.txt")


class Env(TestEnv):
    pass
