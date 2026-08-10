"""Helpers for spec-tests: materialize .jaz fixtures into a tmp dir.

Spec-tests declare each fixture inline as a triple-quoted ``.jaz`` source whose
first line is a ``# <filename>`` directive, and call ``save_fixture(source)``.
The directive names the file; the remaining lines are dedented and written.

Fixtures are written into a per-process tmp dir, under a subdirectory named after
the *calling test module*. This means:

- fixtures never touch the checked-in tree;
- relative imports between fixtures (e.g. ``from ./foo.jaz import ...``) resolve,
  because every fixture saved from one module lands in the same subdir;
- different test modules can reuse the same fixture filename (``foo.jaz``) with
  different content without colliding, since each gets its own subdir.

The subdir is derived automatically from the caller's module ``__name__``, so
test call sites stay ``save_fixture(source)`` with no namespace to thread.
"""

import atexit
import inspect
import os
import shutil
import tempfile
import textwrap

# One tmp dir per test process, created lazily on first use and cleaned up at
# exit. Each caller module gets its own subdir beneath it.
_fixture_dir: str | None = None


def _get_fixture_root() -> str:
    global _fixture_dir
    if _fixture_dir is None:
        _fixture_dir = tempfile.mkdtemp(prefix="jazzoo-fixtures-")
        atexit.register(shutil.rmtree, _fixture_dir, ignore_errors=True)
    return _fixture_dir


def _caller_namespace() -> str:
    """Module name of the first frame outside this file — the calling test module.

    Falls back to "__unknown__" if the caller has no module (e.g. exec'd code).
    """
    for frame_info in inspect.stack()[1:]:
        module = inspect.getmodule(frame_info.frame)
        if module is None or module.__name__ != __name__:
            return module.__name__ if module is not None else "__unknown__"
    return "__unknown__"


def _namespace_dir() -> str:
    path = os.path.join(_get_fixture_root(), _caller_namespace())
    os.makedirs(path, exist_ok=True)
    return path


def _split_directive(source: str) -> tuple[str, str]:
    """Parse the leading ``# <filename>`` directive from a fixture source.

    Returns ``(filename, body)`` where ``body`` is everything after the directive
    line, dedented. Leading blank lines before the directive are ignored so the
    source may start on the line after the opening triple-quote.
    """
    lines = source.splitlines()
    idx = 0
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1
    if idx >= len(lines):
        raise ValueError("Fixture source is empty; expected a leading '# <filename>' line")

    directive = lines[idx].strip()
    if not directive.startswith("#"):
        raise ValueError(
            f"Fixture must start with a '# <filename>' directive; got: {directive!r}"
        )
    filename = directive[1:].strip()
    if not filename:
        raise ValueError("Fixture '# <filename>' directive has no filename")

    body = "\n".join(lines[idx + 1:])
    body = textwrap.dedent(body)
    if body and not body.endswith("\n"):
        body += "\n"
    return filename, body


def save_fixture(source: str) -> str:
    """Write one inline fixture and return its absolute path.

    ``source`` must begin with a ``# <filename>`` directive line naming the file
    (e.g. ``# foo.jaz``). That line is stripped; the remaining body is dedented
    and written under the caller module's fixture subdir. The filename may contain
    subdirectories (e.g. ``sub/foo.jaz``); intermediate dirs are created.
    """
    filename, body = _split_directive(source)
    path = os.path.join(_namespace_dir(), filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    return path
