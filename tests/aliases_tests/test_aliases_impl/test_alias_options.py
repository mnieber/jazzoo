import subprocess
import sys

from aliases_tests.aliases_test_env import Context, TestEnv

from jazzoo.aliases.errors import AliasError

JAZZOO_SOURCE = """
deploy(env="staging"):
    @echo "deploy env=🐆.env"

broken():
    @exit 3
"""

ALIASES = """
[alias]
dep = deploy --confirm
tb = broken --trace
lf = deploy --file=other.jaz
ls = deploy --list
la = deploy --list-all
hp = deploy --help
"""

# Runs the jaz entrypoint with the arguments of the subprocess
RUN_JAZ = (
    "import sys; "
    "from jazzoo.runtime.entrypoints.jazzoo import main; "
    "sys.exit(main(sys.argv[1:]))"
)


def create_env(context: Context):
    return Env(context)


def test_alias_options(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a project with the targets deploy and broken (which fails), and
    # aliases whose expansions have options of jaz.
    if env.step(
        env.write_jazzoo(JAZZOO_SOURCE),
        env.write_aliases(ALIASES),
    ):
        pass

    # We run jaz dep without a controlling terminal.
    #
    # The expansion has --confirm, which needs a terminal, so jaz should fail with
    # that message, and deploy should not run.
    if env.step(
        env.run_jaz_without_terminal("dep"),
    ):
        assert env.exit_code != 0
        assert "--confirm needs a terminal" in env.printed_err
        assert "deploy env=" not in env.output

    # We run jaz --trace dep and jaz dep --trace without a terminal.
    #
    # The option on the command line should be added to the options of the
    # expansion, so --confirm should still apply.
    if env.step(
        env.run_jaz_without_terminal("--trace", "dep"),
    ):
        assert env.exit_code != 0
        assert "--confirm needs a terminal" in env.printed_err

    if env.step(
        env.run_jaz_without_terminal("dep", "--trace"),
    ):
        assert env.exit_code != 0
        assert "--confirm needs a terminal" in env.printed_err

    # We run jaz dep --confirm without a terminal, which gives --confirm twice.
    #
    # The option should count once: jaz should fail as before, not with a usage
    # error.
    if env.step(
        env.run_jaz_without_terminal("dep", "--confirm"),
    ):
        assert env.exit_code != 0
        assert "--confirm needs a terminal" in env.printed_err

    # We run jaz tb, whose expansion has --trace, as the console script does.
    #
    # broken fails, and the stack trace should be printed.
    if env.step(
        env.run_jaz_cli("tb"),
    ):
        assert env.exit_code == 1
        assert "Traceback" in env.printed_err

    # We run the aliases whose expansions have --file, --list, --list-all and
    # --help.
    #
    # These options are not allowed in an expansion, so each should be an
    # AliasError that names the config file, the alias and the option.
    for alias, option in [
        ("lf", "--file"),
        ("ls", "--list"),
        ("la", "--list-all"),
        ("hp", "--help"),
    ]:
        if env.step(
            env.run_jaz_and_catch_error(alias),
        ):
            assert isinstance(env.error, AliasError)
            assert env.error.filename == env.alias_config_file()
            assert f'"{alias}"' in env.error.message
            assert option in env.error.message


class Env(TestEnv):
    def run_jaz_without_terminal(self, *args: str):
        """Runs jaz in a new session, which has no controlling terminal."""
        completed = subprocess.run(
            [sys.executable, "-c", RUN_JAZ, *args],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            start_new_session=True,
            timeout=30,
        )
        self.exit_code = completed.returncode
        self.output = completed.stdout
        self.printed_err = completed.stderr
