from commands_tests.commands_test_env import Context, TestEnv

# Runs four commands, of which the first three are skipped, and prints their results
SCRIPT = """
from jazzoo.commands import run

results = [
    ("plain", run("touch plain.txt")),
    ("captured", run("touch captured.txt; echo out; echo err >&2", capture=True)),
    ("unchecked", run("touch unchecked.txt; exit 3", check=False)),
    ("ran", run("echo ran", capture=True)),
]
for name, result in results:
    print(
        name,
        result.skipped,
        result.returncode,
        repr(result.stdout),
        repr(result.stderr),
        flush=True,
    )
"""


def create_env(context: Context):
    return Env(context)


def test_confirm_skip(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a script that runs a plain command, a captured command, a command with
    # check=False, and a captured command that runs. We switch on the confirmation
    # of commands, run the script, and skip the first three commands.
    #
    # Every command should be confirmed, also the one with check=False. The skipped
    # commands should not have run, so their files should not exist. Their results
    # should say that they were skipped, with exit code 0. A captured command that
    # was skipped should have empty output. The command that ran should not be
    # marked as skipped.
    if env.step(
        env.write_file("script.py", SCRIPT),
        env.set_env("JAZZOO_CONFIRM", "1"),
        env.run_python_script_in_pty("script.py", answers=["n", "n", "n", "y"]),
    ):
        assert env.exit_code == 0, env.pty_output
        assert len(env.prompts) == 4
        assert not env.file_exists("plain.txt")
        assert not env.file_exists("captured.txt")
        assert not env.file_exists("unchecked.txt")
        assert env.pty_lines() == [
            "plain True 0 None None",
            "captured True 0 '' ''",
            "unchecked True 0 None None",
            "ran False 0 'ran\\n' ''",
        ]

    # We switch off the confirmation of commands, and run a command.
    #
    # Its result should not be marked as skipped.
    if env.step(
        env.unset_env("JAZZOO_CONFIRM"),
        env.run("true"),
    ):
        assert env.result.skipped is False


class Env(TestEnv):
    pass
