import os
import typing as T

from jazzoo_test_env import Context, TestEnv as JazzooTestEnv

from jazzoo.runtime.entrypoints.jazzoo import main, run as run_jaz

__all__ = ["Context", "TestEnv", "SHOP_JAZZOO", "SHOP_ALIASES"]

# The jazzoo file of most tests: two targets, a private function, and the layers fe
# (with the nested layer lint) and db.
SHOP_JAZZOO = """
from ./fe.jaz export (build, test, lint) as fe
from ./db.jaz export (migrate,) as db

build(mode="debug", watch="no"):
    @echo "build mode=🐆.mode watch=🐆.watch"

deploy():
    @echo "deploy"

[private]
_prepare():
    @echo "prepare"
"""

FE_JAZ = """
from ./lint.jaz export (check, fix) as lint

build(mode="release"):
    @echo "fe.build mode=🐆.mode"

test():
    @echo "fe.test"
"""

LINT_JAZ = """
check():
    @echo "fe.lint.check"

fix():
    @echo "fe.lint.fix"
"""

DB_JAZ = """
migrate():
    @echo "db.migrate"
"""

# The aliases of most tests. The alias build is left out of the completions,
# because the target build wins.
SHOP_ALIASES = """
[alias]
b = build
fb = fe.build mode=debug
build = deploy
dep = deploy --confirm
"""


class TestEnv(JazzooTestEnv):
    def __post_init__(self):
        self.printed_err: T.Optional[str] = None
        self.system_exit: T.Optional[SystemExit] = None

        # The alias config file goes below tmp_path, never into the home directory
        # of the developer.
        os.makedirs(self.path("home"), exist_ok=True)
        self.set_env("HOME", self.path("home"))
        self.unset_env("XDG_CONFIG_HOME")

    def write_jazzoo(self, text: str = SHOP_JAZZOO):
        """Writes the jazzoo file of the project directory shop (with the libraries
        fe.jaz, lint.jaz and db.jaz), and changes to that directory."""
        self.write_file("shop/jazzoo", text)
        self.write_file("shop/fe.jaz", FE_JAZ)
        self.write_file("shop/lint.jaz", LINT_JAZ)
        self.write_file("shop/db.jaz", DB_JAZ)
        self.change_dir("shop")

    def write_aliases(self, text: str = SHOP_ALIASES):
        """Writes the alias config file in ~/.config/jazzoo."""
        self.write_file("home/.config/jazzoo/config", text)

    def make_dir(self, name: str):
        os.makedirs(self.path(name), exist_ok=True)

    def complete_jaz(self, *words: str):
        """Runs `jaz --complete -- <words>` as fish does: through the console
        script, so that an error would be printed, not raised. The last word is the
        one that is being completed."""
        self.run_jaz_cli("--complete", "--", *words)

    def run_jaz(self, *args: str):
        """Runs jaz in-process, and stores the exit code and what was printed."""
        self.context.capsys.readouterr()
        try:
            self.exit_code = run_jaz(list(args))
        finally:
            self.output, self.printed_err = self.context.capsys.readouterr()

    def run_jaz_and_catch_exit(self, *args: str):
        self.system_exit = None
        try:
            self.run_jaz(*args)
        except SystemExit as system_exit:
            self.system_exit = system_exit

    def run_jaz_cli(self, *args: str):
        """Runs jaz as the console script does: errors are printed, not raised."""
        self.context.capsys.readouterr()
        self.exit_code = main(list(args))
        self.output, self.printed_err = self.context.capsys.readouterr()

    # Queries

    def output_lines(self) -> T.List[str]:
        return (self.output or "").splitlines()

    def candidates(self) -> T.List[str]:
        """The printed candidates without their descriptions, in the printed
        order."""
        return [line.split("\t")[0] for line in self.output_lines()]

    def descriptions(self) -> T.Dict[str, T.Optional[str]]:
        """A dict from candidate to description (None when it has none)."""
        result: T.Dict[str, T.Optional[str]] = {}
        for line in self.output_lines():
            candidate, separator, description = line.partition("\t")
            result[candidate] = description if separator else None
        return result
