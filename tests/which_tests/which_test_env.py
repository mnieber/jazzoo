import os
import typing as T

from jazzoo_test_env import Context, TestEnv as JazzooTestEnv

from jazzoo.runtime.entrypoints.jazzoo import main, run as run_jaz

__all__ = ["Context", "TestEnv", "SHOP_JAZZOO"]

# The jazzoo file of most tests: the target build, the target deploy that is
# defined in tools.jaz, and the layer fe. The targets echo their name, so that a
# test sees whether a target ran.
SHOP_JAZZOO = """
from ./tools.jaz export deploy
from ./fe/fe.jaz export * as fe

build(mode="release"):
    @echo "build mode=🐆.mode"
"""

TOOLS_JAZ = """
deploy():
    @echo "deploy"
"""

# The layer fe defines build, and re-exports lint from lint.jaz
FE_JAZ = """
from ./lint.jaz export lint

build(mode="release"):
    @echo "fe.build mode=🐆.mode"
"""

LINT_JAZ = """
lint():
    @echo "fe.lint"
"""


class TestEnv(JazzooTestEnv):
    def __post_init__(self):
        self.printed_err: T.Optional[str] = None

        # The alias config file goes below tmp_path, never into the home directory
        # of the developer.
        os.makedirs(self.path("home"), exist_ok=True)
        self.set_env("HOME", self.path("home"))
        self.unset_env("XDG_CONFIG_HOME")

    def write_jazzoo(self, text: str = SHOP_JAZZOO):
        """Writes the jazzoo file of the project directory shop (with the libraries
        tools.jaz, fe/fe.jaz and fe/lint.jaz), and changes to that directory."""
        self.write_file("shop/jazzoo", text)
        self.write_file("shop/tools.jaz", TOOLS_JAZ)
        self.write_file("shop/fe/fe.jaz", FE_JAZ)
        self.write_file("shop/fe/lint.jaz", LINT_JAZ)
        self.change_dir("shop")

    def write_aliases(self, text: str):
        """Writes the alias config file in ~/.config/jazzoo."""
        self.write_file("home/.config/jazzoo/config", text)

    def run_jaz(self, *args: str):
        """Runs jaz in-process, and stores the exit code and what was printed."""
        self.context.capsys.readouterr()
        try:
            self.exit_code = run_jaz(list(args))
        finally:
            self.output, self.printed_err = self.context.capsys.readouterr()

    def run_jaz_and_catch_error(self, *args: str):
        self.error = None
        try:
            self.run_jaz(*args)
        except Exception as error:
            self.error = error

    def run_jaz_cli(self, *args: str):
        """Runs jaz as the console script does: errors are printed, not raised."""
        self.context.capsys.readouterr()
        self.exit_code = main(list(args))
        self.output, self.printed_err = self.context.capsys.readouterr()

    # Queries

    def output_lines(self) -> T.List[str]:
        return (self.output or "").splitlines()
