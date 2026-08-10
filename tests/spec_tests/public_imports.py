from jazzoo.modules.rules.parse_module import parse_module
from jazzoo.modules.rules.get_function_by_path import get_function_by_path
from jazzoo.modules.rules.get_targets import get_targets
from jazzoo.runtime.utils.test_utils import save_fixture

# A library module used as the export source. It exports two functions and
# privately imports something of its own to exercise export-* non-transitivity.
save_fixture("""# foo.jaz
🐐.test = 123
🐭.test = "mouse"

from ./helper.jaz import secret as _h

bar():
    #!/usr/bin/env bash
    echo 🐭.test

okay():
    #!/usr/bin/env bash
    echo "okay"
""")

# A second-level module that foo.jaz privately imports from. Its `secret` must
# NOT leak through `from ./foo.jaz export *`.
save_fixture("""# helper.jaz
secret():
    #!/usr/bin/env bash
    echo "secret"
""")


def test_export_single():
    jazzoo_fn = save_fixture("""# test_export_single.jaz
    from ./foo.jaz export bar
    """)
    root_module = parse_module(jazzoo_fn)

    # Flat in root: 🐭.bar(), not 🐭.foo.bar().
    fn = get_function_by_path(root_module, "bar")
    assert fn is not None
    assert fn.is_target is True

    # Listed: it's a direct-member target of the root module.
    assert "bar" in [f.name for f in get_targets(root_module)]


def test_export_alias():
    jazzoo_fn = save_fixture("""# test_export_alias.jaz
    from ./foo.jaz export bar as hello
    """)
    root_module = parse_module(jazzoo_fn)

    assert get_function_by_path(root_module, "hello") is not None
    assert get_function_by_path(root_module, "bar") is None
    assert "hello" in [f.name for f in get_targets(root_module)]


def test_export_tuple():
    jazzoo_fn = save_fixture("""# test_export_tuple.jaz
    from ./foo.jaz export (bar, okay)
    """)
    root_module = parse_module(jazzoo_fn)

    names = {f.name for f in get_targets(root_module)}
    assert names == {"bar", "okay"}


def test_export_star():
    jazzoo_fn = save_fixture("""# test_export_star.jaz
    from ./foo.jaz export *
    """)
    root_module = parse_module(jazzoo_fn)

    names = {f.name for f in get_targets(root_module)}
    # export * pulls in foo's own exports only...
    assert names == {"bar", "okay"}
    # ...never the functions foo merely imported privately.
    assert get_function_by_path(root_module, "secret") is None
