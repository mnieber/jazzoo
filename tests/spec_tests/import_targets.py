from jazzoo.modules.rules.parse_module import parse_module
from jazzoo.modules.rules.get_child_module_by_name import get_child_module_by_name
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


def test_import_target_not_listed_at_root():
    # Root privately imports foo; foo.bar is a target intrinsically, but is
    # nested under the alias sub-module rather than a direct member of root.
    jazzoo_fn = save_fixture("""# test_import_not_listed.jaz
    from ./foo.jaz import bar as baz
    """)
    root_module = parse_module(jazzoo_fn)

    baz_module = get_child_module_by_name(root_module, "baz")
    bar = get_function_by_path(root_module, "baz.bar")

    # Intrinsic target-ness survives the import...
    assert bar.is_target is True
    # ...but listability requires being a direct member of the root module.
    assert bar not in get_targets(root_module)
    assert get_targets(root_module) == []
    # The sub-module's own targets do not surface at the root either.
    assert bar in get_targets(baz_module)
