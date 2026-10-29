from zoo_tests.zoo_test_env import Context, TestEnv

from jazzoo.runtime.entrypoints.jazzoo import run as run_jaz

JAZZOO = """
from ./lib/lib.jaz export lib-dirs

🐭.started-in = ⚙️.invocation_dir

dirs():
    @echo "invocation_dir=⚙️.invocation_dir"
    @echo "root_dir=⚙️.root_module.dirname"
    @echo "started_in=🐭.started-in"

show(path):
    @cat {{ ⚙️.invocation_dir / 🐆.path }}
"""

LIB_JAZ = """
lib-dirs():
    @echo "lib_invocation_dir=⚙️.invocation_dir"
"""


def create_env(context: Context):
    return Env(context)


def test_invocation_dir(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the project shop, whose jazzoo file prints ⚙️.invocation_dir in a
    # target, in a top-level assignment, and in a target of an imported module.
    if env.step(
        env.add_project("shop", JAZZOO),
        env.write_file("projects/shop/lib/lib.jaz", LIB_JAZ),
        env.make_dir("elsewhere"),
    ):
        pass

    # We run `jaz dirs` in the project directory.
    #
    # ⚙️.invocation_dir should be the current directory, which here is also the
    # directory of the root module. A top-level assignment sees the same value.
    if env.step(
        env.change_dir("projects/shop"),
        env.run_jaz("dirs"),
    ):
        assert env.output.splitlines() == [
            "invocation_dir=" + env.path("projects/shop"),
            "root_dir=" + env.path("projects/shop"),
            "started_in=" + env.path("projects/shop"),
        ]

    # We run `jaz --file projects/shop/jazzoo dirs` in tmp_path.
    #
    # Now ⚙️.invocation_dir is tmp_path, and differs from the directory of the
    # root module.
    if env.step(
        env.change_dir(""),
        env.run_jaz("--file", "projects/shop/jazzoo", "dirs"),
    ):
        assert env.output.splitlines() == [
            "invocation_dir=" + env.path(""),
            "root_dir=" + env.path("projects/shop"),
            "started_in=" + env.path(""),
        ]

    # We run the target of the imported module.
    #
    # ⚙️.invocation_dir belongs to the run, not to the module, so it should be
    # the same as in the root module.
    if env.step(
        env.change_dir(""),
        env.run_jaz("--file", "projects/shop/jazzoo", "lib-dirs"),
    ):
        assert env.output == "lib_invocation_dir=" + env.path("") + "\n"

    # We register shop, and in another directory, we pass the relative path of a
    # file in that directory to a target that joins it with ⚙️.invocation_dir.
    #
    # The target runs in the project directory, but should still find the file.
    if env.step(
        env.init_env("shop"),
        env.use_zoo_of("projects/shop/.venv"),
        env.write_file("elsewhere/notes.txt", "my notes\n"),
        env.change_dir("elsewhere"),
        env.run_zoo("show", "notes.txt"),
    ):
        assert env.output == "my notes\n"


class Env(TestEnv):
    def run_jaz(self, *args: str):
        """Runs jaz in-process, and stores what it printed."""
        self.context.capsys.readouterr()
        self.exit_code = run_jaz(list(args))
        self.output, self.printed_err = self.context.capsys.readouterr()
