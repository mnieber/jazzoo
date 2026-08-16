"""The installed `jaz` / `jazzoo` console scripts.

Every other CLI test calls `main()` in-process, which leaves the console-script
entry points and their pyproject wiring untested - a broken `[project.scripts]`
would not fail the suite. These run the real binary in a subprocess.

Skipped when the package is not installed, so a bare checkout still runs green.
"""

import os
import shutil
import subprocess

import pytest

from jazzoo.runtime.utils.test_utils import save_fixture

_JAZ = shutil.which("jaz")

pytestmark = pytest.mark.skipif(
    _JAZ is None, reason="jaz is not on PATH; install the package to run these"
)


def _run(args, cwd):
    return subprocess.run(
        [_JAZ, *args], cwd=cwd, capture_output=True, text=True
    )


def test_the_installed_binary_lists_and_runs_targets():
    """`jaz --list` and `jaz <target>` work through the console script."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_installed_cli.jaz
        build(target="app"):
            @echo "built 🐆.target"

        [private]
        _hidden():
            @echo "nope"
        """)
        directory = os.path.dirname(jazzoo_fn)

        # Run
        listed = _run(["--file", jazzoo_fn, "--list"], directory)
        ran = _run(["--file", jazzoo_fn, "build", "target=myapp"], directory)

        # Assert
        assert listed.returncode == 0
        assert "build" in listed.stdout
        assert "_hidden" not in listed.stdout

        assert ran.returncode == 0
        assert "built myapp" in ran.stdout


def test_the_installed_binary_reports_errors_on_stderr():
    """A JazzooError prints its location to stderr and exits non-zero."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_installed_cli_error.jaz
        build():
            @echo "fine"
        """)
        directory = os.path.dirname(jazzoo_fn)

        # Run
        result = _run(["--file", jazzoo_fn, "no-such-target"], directory)

        # Assert
        assert result.returncode != 0
        assert "no-such-target" in result.stderr


def test_the_jazzoo_alias_is_installed_too():
    """pyproject registers both `jaz` and `jazzoo` for the same entry point."""
    if True:
        # Config
        alias = shutil.which("jazzoo")

        # Assert
        assert alias is not None
