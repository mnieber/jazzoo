import os
import typing as T

from jazzoo_test_env import Context, TestEnv as JazzooTestEnv

from jazzoo.runtime.entrypoints.jazzoo import main, run as run_jaz

__all__ = ["Context", "TestEnv", "SHOP_JAZZOO"]

# The jazzoo file of most tests. The targets echo their name and arguments, so that
# a test sees which target ran, and with which arguments.
SHOP_JAZZOO = """
from ./fe.jaz export (build,) as fe

build(mode="release"):
    @echo "build mode=🐆.mode"

greet(name, greeting="hello"):
    @echo "greet name=🐆.name greeting=🐆.greeting"
"""

FE_JAZ = """
build(mode="release"):
    @echo "fe.build mode=🐆.mode"
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
        """Writes the jazzoo file of the project directory shop (with the library
        fe.jaz), and changes to that directory."""
        self.write_file("shop/jazzoo", text)
        self.write_file("shop/fe.jaz", FE_JAZ)
        self.change_dir("shop")

    def write_aliases(self, text: str, path: str = "home/.config/jazzoo/config"):
        """Writes the alias config file (by default in ~/.config/jazzoo)."""
        self.write_file(path, text)

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

    def alias_config_file(self) -> str:
        return self.path("home/.config/jazzoo/config")
