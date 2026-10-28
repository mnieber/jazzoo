"""Loading a dotenv file into the environment with ⚙️.load_env.

`⚙️.load_env(path=...)` is a statement: it reads `KEY=VALUE` lines from a file and
exports them into the environment, so that `⚙️.env` sees them and every later
subprocess inherits them. It yields no value of its own.
"""

import os

import pytest

from jazzoo import ExecutionError, ResolutionError, evaluate, parse_module
from jazzoo.runtime.utils.test_utils import save_fixture

save_fixture("""# app.env
# Comments and blank lines are skipped.

JAZZOO_DOTENV_SHELL=fish
JAZZOO_DOTENV_PACKAGES="nano curl fish"
JAZZOO_DOTENV_GREETING='hello there'
""")


@pytest.fixture(autouse=True)
def restore_environment():
    """⚙️.load_env changes os.environ, so every test starts and ends with the same
    environment."""
    saved = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(saved)


def test_load_env_exports_variables_to_the_environment():
    """A module-level ⚙️.load_env runs when the module is loaded. Its variables are
    then visible through ⚙️.env, and inherited by subprocesses. Surrounding quotes
    are stripped from a value."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_load_env_module_level.jaz
        ⚙️.load_env(path=⚙️.module.dirname / "app.env")

        show():
            echo "⚙️.env.JAZZOO_DOTENV_SHELL|$JAZZOO_DOTENV_PACKAGES|⚙️.env.JAZZOO_DOTENV_GREETING"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.show()") == "fish|nano curl fish|hello there"
        assert os.environ["JAZZOO_DOTENV_SHELL"] == "fish"


def test_load_env_does_not_override_the_existing_environment(monkeypatch):
    """A variable that is already set keeps its value, so the environment can
    override what the file says (e.g. `JAZZOO_DOTENV_SHELL=bash jaz show`)."""
    if True:
        # Config
        monkeypatch.setenv("JAZZOO_DOTENV_SHELL", "bash")
        jazzoo_fn = save_fixture("""# test_load_env_no_override.jaz
        ⚙️.load_env(path=⚙️.module.dirname / "app.env")

        show():
            echo "⚙️.env.JAZZOO_DOTENV_SHELL ⚙️.env.JAZZOO_DOTENV_GREETING"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.show()") == "bash hello there"


def test_load_env_in_a_function_body_affects_the_lines_after_it():
    """⚙️.load_env may also be used as a statement in a function body. It takes
    effect when that line runs."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_load_env_in_body.jaz
        show():
            🐆.before = ⚙️.env.JAZZOO_DOTENV_SHELL?:-unset
            ⚙️.load_env(path=⚙️.module.dirname / "app.env")
            echo "🐆.before ⚙️.env.JAZZOO_DOTENV_SHELL"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.show()") == "unset fish"


def test_load_env_requires_the_file_by_default():
    """A missing file is an ExecutionError, so a misspelled path is caught. With
    `required=false` a missing file is skipped and nothing is loaded."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_load_env_missing.jaz
        strict():
            ⚙️.load_env(path=⚙️.module.dirname / "missing.env")

        lenient():
            ⚙️.load_env(path=⚙️.module.dirname / "missing.env", required=false)
            echo "loaded nothing"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        with pytest.raises(ExecutionError):
            evaluate(root_module, "🐭.strict()")
        assert evaluate(root_module, "🐭.lenient()") == "loaded nothing"
