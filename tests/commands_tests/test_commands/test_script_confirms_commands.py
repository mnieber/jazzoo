from commands_tests.commands_test_env import Context, TestEnv

SCRIPT = """
from jazzoo.commands import run

run("echo built")
result = run("touch migrated.txt")
print(f"migrate skipped={result.skipped}", flush=True)
run(["echo", "deployed"])
run("echo cleaned-up")
"""


def create_env(context: Context):
    return Env(context)


def test_script_confirms_commands(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a deploy script that runs four commands. We switch on the confirmation
    # of commands, and run the script in a terminal. We answer y to the first
    # prompt, n to the second and q to the third.
    #
    # Each command should be shown with its directory before it runs. The first
    # command should have run. The second should have been skipped, and the script
    # should have continued. The third answer should have aborted the script with a
    # CommandAbortedError, so the third and fourth commands never ran.
    if env.step(
        env.write_file("deploy.py", SCRIPT),
        env.set_env("JAZZOO_CONFIRM", "1"),
        env.run_python_script_in_pty("deploy.py", answers=["y", "n", "q"]),
    ):
        assert env.prompts == [
            f"({env.path('')}) echo built",
            f"({env.path('')}) touch migrated.txt",
            f"({env.path('')}) echo deployed",
        ]
        assert env.pty_lines()[:2] == ["built", "migrate skipped=True"]
        assert not env.file_exists("migrated.txt")
        assert "deployed" not in env.pty_lines()
        assert "cleaned-up" not in env.pty_lines()
        assert env.exit_code != 0
        assert "CommandAbortedError" in env.pty_output

    # We switch off the confirmation of commands, and run the script again.
    #
    # All commands should run without a prompt.
    if env.step(
        env.unset_env("JAZZOO_CONFIRM"),
        env.run_python_script_in_pty("deploy.py"),
    ):
        assert env.exit_code == 0, env.pty_output
        assert env.prompts == []
        assert env.pty_lines() == [
            "built",
            "migrate skipped=False",
            "deployed",
            "cleaned-up",
        ]
        assert env.file_exists("migrated.txt")


class Env(TestEnv):
    pass
