"""Helpers for spec-tests: materialize .jaz fixtures into a tmp dir.

Spec-tests declare their fixtures as a name -> .jaz-source dict and call
``save_fixtures(fixtures)`` once at module import time. Each test then resolves a
fixture by name with ``get_fixture_fn(name)``. Both share a single per-process
tmp directory so that:

- fixtures never touch the checked-in tree, and
- relative imports between fixtures (e.g. ``from ./foo.jaz import ...``) resolve,
  because every fixture in one ``save_fixtures`` call lands in the same dir.
"""

import atexit
import os
import shutil
import tempfile

# One tmp dir per test process, created lazily on first use and cleaned up at
# exit. Shared by save_fixtures (writes) and get_fixture_fn (reads).
_fixture_dir: str | None = None


def _get_fixture_dir() -> str:
    global _fixture_dir
    if _fixture_dir is None:
        _fixture_dir = tempfile.mkdtemp(prefix="jazzoo-fixtures-")
        atexit.register(shutil.rmtree, _fixture_dir, ignore_errors=True)
    return _fixture_dir


def save_fixtures(fixtures: dict[str, str]) -> str:
    """Write each ``name -> source`` fixture into the shared tmp dir.

    ``name`` may contain subdirectories (e.g. ``sub/foo.jaz``); intermediate
    directories are created. Leading whitespace/newlines in the source are
    stripped so fixtures can be written as triple-quoted blocks starting on the
    line after the opening quotes. Returns the tmp dir path.
    """
    fixture_dir = _get_fixture_dir()
    for name, source in fixtures.items():
        path = os.path.join(fixture_dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(source.lstrip("\n"))
    return fixture_dir


def get_fixture_fn(name: str) -> str:
    """Return the absolute path of a fixture previously saved under ``name``."""
    path = os.path.join(_get_fixture_dir(), name)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Fixture {name!r} not found in {_get_fixture_dir()}; "
            "did you pass it to save_fixtures()?"
        )
    return path
