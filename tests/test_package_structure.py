"""Structural invariants of the jazzoo package itself.

These do not exercise the language; they keep the package layout honest.
"""

import pathlib
import re

import jazzoo


def test_no_submodule_imports_from_the_package_root():
    """Modules under jazzoo/ must import by full submodule path, never
    `from jazzoo import X`. The latter reads an attribute off a partially
    initialized package while __init__.py is still running, which is a circular
    import waiting to happen."""
    if True:
        # Config
        root = pathlib.Path(jazzoo.__file__).parent

        # Run
        offenders = [
            str(path.relative_to(root))
            for path in root.rglob("*.py")
            if path.name != "__init__.py"
            and re.search(r"^from jazzoo import ", path.read_text(encoding="utf-8"), re.M)
        ]

        # Assert
        assert offenders == []


def test_the_facade_exports_every_public_name():
    """The public surface is defined in one place, so anything the tests import
    from `jazzoo` must be listed in __all__."""
    if True:
        # Config
        expected = {
            "ArgumentError",
            "ExecutionError",
            "JazzooError",
            "ModuleImportError",
            "ParseError",
            "ResolutionError",
            "evaluate",
            "get_function_by_path",
            "get_module_by_path",
            "get_targets",
            "parse_module",
        }

        # Assert
        assert set(jazzoo.__all__) == expected
        for name in expected:
            assert hasattr(jazzoo, name)
