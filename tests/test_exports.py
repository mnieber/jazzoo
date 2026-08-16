import pytest

from jazzoo import get_function_by_path, get_targets, parse_module
from jazzoo.runtime.utils.test_utils import save_fixture

pytestmark = pytest.mark.stage(4)

# A library module used as the export source. It exports two of its own
# functions (bar, okay), re-exports one function from helper.jaz (some_target),
# and privately imports another (other).
save_fixture("""# foo.jaz
🐐.test = 123
🐭.test = "mouse"

from ./helper.jaz import other as _h
from ./helper.jaz export some_target

bar():
    #!/usr/bin/env bash
    echo 🐭.test

okay():
    #!/usr/bin/env bash
    echo "okay"
""")

# A second-level module.
save_fixture("""# helper.jaz
some_target():
    #!/usr/bin/env bash
    echo "some_target"

other():
    #!/usr/bin/env bash
    echo "other"
""")


def test_export_single():
    """When you export a function (bar) then it should be marked as a target
    and appear in the list of targets.
    """
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_export_single.jaz
        from ./foo.jaz export bar
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        fn = get_function_by_path(root_module, "bar")

        # Assert
        assert fn is not None
        assert fn.is_target is True
        assert "bar" in [f.name for f in get_targets(root_module)]

    """This also works when using an alias"""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_export_alias.jaz
        from ./foo.jaz export bar as hello
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert get_function_by_path(root_module, "hello") is not None
        assert get_function_by_path(root_module, "bar") is None
        assert "hello" in [f.name for f in get_targets(root_module)]


def test_reexported_function_is_a_target_of_foo():
    """A function foo.jaz re-exports from helper.jaz becomes a target of foo."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_reexport.jaz
        from ./foo.jaz export some_target
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        fn = get_function_by_path(root_module, "some_target")

        # Assert
        assert fn is not None
        assert fn.is_target is True
        assert "some_target" in [f.name for f in get_targets(root_module)]


def test_export_tuple():
    """A tuple is used when you want to export multiple functions at once."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_export_tuple.jaz
        from ./foo.jaz export (bar, okay)
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        names = {f.name for f in get_targets(root_module)}
        assert names == {"bar", "okay"}


def test_export_star():
    """You can export all target functions from a module using the `*` syntax."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_export_star.jaz
        from ./foo.jaz export *
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        names = {f.name for f in get_targets(root_module)}
        assert names == {"bar", "okay", "some_target"}
        # `other` was only privately imported by foo, so it does not leak.
        assert get_function_by_path(root_module, "other") is None


def test_targets_and_re_exported_targets_are_listed():
    """Targets and re-exported targets are listed by `jaz --list`."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_import_reexported.jaz
        from ./foo.jaz export (bar as baz,)

        qux():
            #!/usr/bin/env bash
            echo "qux"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        baz = get_function_by_path(root_module, "baz")
        qux = get_function_by_path(root_module, "qux")

        # Assert
        assert baz.is_target is True
        assert baz in get_targets(root_module)
        assert qux.is_target is True
        assert qux in get_targets(root_module)
