import os
from jazzoo.modules.rules.parse_module import parse_module
from jazzoo.modules.rules.get_child_module_by_name import get_child_module_by_name
from jazzoo.modules.rules.get_function_by_path import get_function_by_path
from jazzoo.modules.rules.get_targets import get_targets
from jazzoo.modules.rules.eval import eval
from jazzoo.runtime.utils.test_utils import get_fixture_fn, save_fixtures

fixtures = {}

# A library module used as the import/export source throughout. It exports two
# functions, defines a 🐭 (module) var and a 🐐 (global) var, and privately
# imports something of its own to exercise export-* non-transitivity.
fixtures["foo.jaz"] = """
🐐.test = 123
🐭.test = "mouse"

from ./helper.jaz import secret as _h

bar():
    #!/usr/bin/env bash
    echo 🐭.test

okay():
    #!/usr/bin/env bash
    echo "okay"
"""

# A second-level module that foo.jaz privately imports from. Its `secret` must
# NOT leak through `from ./foo.jaz export *`.
fixtures["helper.jaz"] = """
secret():
    #!/usr/bin/env bash
    echo "secret"
"""

# --- Private imports (import ... as ns) ------------------------------------

fixtures["test_single_import.jaz"] = """
from ./foo.jaz import bar as baz
"""

fixtures["test_import_tuple.jaz"] = """
from ./foo.jaz import (bar, okay) as baz
"""

fixtures["test_import_symbol_alias.jaz"] = """
from ./foo.jaz import (bar as hello, okay) as baz
"""

fixtures["test_import_star.jaz"] = """
from ./foo.jaz import * as foo
"""

# --- Public exports (export ...) -------------------------------------------

fixtures["test_export_single.jaz"] = """
from ./foo.jaz export bar
"""

fixtures["test_export_alias.jaz"] = """
from ./foo.jaz export bar as hello
"""

fixtures["test_export_tuple.jaz"] = """
from ./foo.jaz export (bar, okay)
"""

fixtures["test_export_star.jaz"] = """
from ./foo.jaz export *
"""

# --- Scoping across the import boundary ------------------------------------

# Caller defines its own 🐭.test; the imported bar() must still resolve 🐭.test
# against foo.jaz, not against the caller.
fixtures["test_mouse_resolves_against_definer.jaz"] = """
🐭.test = "caller"

from ./foo.jaz import bar as baz
"""

# A module whose function reads and writes 🐐 to prove globals are shared.
fixtures["glob.jaz"] = """
touch():
    #!/usr/bin/env bash
    echo 🐐.shared
"""

fixtures["test_global_shared.jaz"] = """
🐐.shared = "from-root"

from ./glob.jaz import touch as g
"""

save_fixtures(fixtures)


# ---------------------------------------------------------------------------
# Private imports: land nested under the alias sub-module, are NOT targets,
# and do NOT appear in `jaz --list`.
# ---------------------------------------------------------------------------

def test_single_import():
    jazzoo_fn = get_fixture_fn("test_single_import.jaz")

    root_module = parse_module(jazzoo_fn)
    foo_module = get_child_module_by_name(root_module, "baz")

    # The alias sub-module is named after the import alias ("baz"), and its
    # filename points at the resolved source file.
    assert foo_module.filename == os.path.join(os.path.dirname(jazzoo_fn), "foo.jaz")

    # 🐐 is shared/global; 🐭 resolves against the imported file.
    assert eval(root_module, "🐐.test") == "123"
    assert eval(foo_module, "🐭.test") == "mouse"

    # Callable as 🐭.baz.bar(), but private: not a target, not listed.
    fn = get_function_by_path(root_module, "baz.bar")
    assert fn.is_target is False
    assert get_targets(root_module) == []


def test_import_tuple():
    jazzoo_fn = get_fixture_fn("test_import_tuple.jaz")
    root_module = parse_module(jazzoo_fn)

    # Both symbols placed under the shared alias sub-module.
    assert get_function_by_path(root_module, "baz.bar") is not None
    assert get_function_by_path(root_module, "baz.okay") is not None

    # Still private — nothing listed at root.
    assert get_targets(root_module) == []


def test_import_symbol_alias():
    jazzoo_fn = get_fixture_fn("test_import_symbol_alias.jaz")
    root_module = parse_module(jazzoo_fn)

    # `bar as hello` → reachable as hello, original name gone.
    assert get_function_by_path(root_module, "baz.hello") is not None
    assert get_function_by_path(root_module, "baz.bar") is None
    # Non-aliased sibling keeps its name.
    assert get_function_by_path(root_module, "baz.okay") is not None


def test_import_star():
    jazzoo_fn = get_fixture_fn("test_import_star.jaz")
    root_module = parse_module(jazzoo_fn)

    # All of foo's exported functions land under the alias sub-module.
    assert get_function_by_path(root_module, "foo.bar") is not None
    assert get_function_by_path(root_module, "foo.okay") is not None
    # A privately-imported symbol of foo (_h.secret) is NOT re-exported by *.
    assert get_function_by_path(root_module, "foo.secret") is None
    assert get_targets(root_module) == []


# ---------------------------------------------------------------------------
# Public exports: land flat in the root module's 🐭, are targets, and DO appear
# in `jaz --list`.
# ---------------------------------------------------------------------------

def test_export_single():
    jazzoo_fn = get_fixture_fn("test_export_single.jaz")
    root_module = parse_module(jazzoo_fn)

    # Flat in root: 🐭.bar(), not 🐭.foo.bar().
    fn = get_function_by_path(root_module, "bar")
    assert fn is not None
    assert fn.is_target is True

    # Listed: it's a direct-member target of the root module.
    assert "bar" in [f.name for f in get_targets(root_module)]


def test_export_alias():
    jazzoo_fn = get_fixture_fn("test_export_alias.jaz")
    root_module = parse_module(jazzoo_fn)

    assert get_function_by_path(root_module, "hello") is not None
    assert get_function_by_path(root_module, "bar") is None
    assert "hello" in [f.name for f in get_targets(root_module)]


def test_export_tuple():
    jazzoo_fn = get_fixture_fn("test_export_tuple.jaz")
    root_module = parse_module(jazzoo_fn)

    names = {f.name for f in get_targets(root_module)}
    assert names == {"bar", "okay"}


def test_export_star():
    jazzoo_fn = get_fixture_fn("test_export_star.jaz")
    root_module = parse_module(jazzoo_fn)

    names = {f.name for f in get_targets(root_module)}
    # export * pulls in foo's own exports only...
    assert names == {"bar", "okay"}
    # ...never the functions foo merely imported privately.
    assert get_function_by_path(root_module, "secret") is None


# ---------------------------------------------------------------------------
# `jaz --list` visibility: only direct-member targets of the ROOT module show.
# A target defined in an imported (non-root) module is not listed there.
# ---------------------------------------------------------------------------

def test_export_target_of_imported_module_not_listed_at_root():
    # test_single_import privately imports foo; foo's bar() is intrinsically a
    # target (not [private]), but is_target alone does not make it listable —
    # listability requires being a direct member of the root module.
    jazzoo_fn = get_fixture_fn("test_single_import.jaz")
    root_module = parse_module(jazzoo_fn)

    baz_module = get_child_module_by_name(root_module, "baz")
    bar = get_function_by_path(root_module, "baz.bar")
    assert bar.is_target is True          # intrinsic property survives import
    assert bar not in get_targets(root_module)   # but not listed at root
    # And the sub-module's own listing does not surface at the root either.
    assert get_targets(root_module) == []


# ---------------------------------------------------------------------------
# Scoping across the import boundary.
# ---------------------------------------------------------------------------

def test_mouse_resolves_against_definer():
    jazzoo_fn = get_fixture_fn("test_mouse_resolves_against_definer.jaz")
    root_module = parse_module(jazzoo_fn)
    foo_module = get_child_module_by_name(root_module, "baz")

    # Same-named 🐭.test in both scopes; each resolves independently.
    assert eval(root_module, "🐭.test") == "caller"
    assert eval(foo_module, "🐭.test") == "mouse"


def test_global_shared_across_modules():
    jazzoo_fn = get_fixture_fn("test_global_shared.jaz")
    root_module = parse_module(jazzoo_fn)
    glob_module = get_child_module_by_name(root_module, "g")

    # 🐐 set in the root is visible from the imported module's scope.
    assert eval(root_module, "🐐.shared") == "from-root"
    assert eval(glob_module, "🐐.shared") == "from-root"
