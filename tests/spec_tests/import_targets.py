from jazzoo.modules.rules.parse_module import parse_module
from jazzoo.modules.rules.get_module_by_path import get_module_by_path
from jazzoo.modules.rules.get_function_by_path import get_function_by_path
from jazzoo.modules.rules.get_targets import get_targets
from jazzoo.runtime.utils.test_utils import save_fixture

# ---------------------------------------------------------------------------
# `jaz --list` visibility rule: a function is listed iff it is intrinsically a
# target (not [private]) AND a direct member of the ROOT module. A target
# defined in an imported (non-root) module keeps is_target == True but is not
# listed, because it is not a direct member of root.
# ---------------------------------------------------------------------------

save_fixture("""# foo.jaz
bar():
    #!/usr/bin/env bash
    echo "bar"
""")


def test_targets_from_imported_modules_are_not_listed():
    """Targets from imported modules are not targets of the root module, and
    are not listed by `jaz --list`."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_import_not_listed.jaz
        from ./foo.jaz import bar as baz
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        baz_module = get_module_by_path(root_module, "baz")
        bar = get_function_by_path(root_module, "baz.bar")

        # Assert
        assert bar.is_target is True
        assert bar not in get_targets(root_module)
        assert get_targets(root_module) == []
        assert bar in get_targets(baz_module)


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
