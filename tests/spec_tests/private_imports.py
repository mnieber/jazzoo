import os
from jazzoo.modules.rules.parse_module import parse_module
from jazzoo.modules.rules.get_child_module_by_name import get_child_module_by_name
from jazzoo.modules.rules.get_function_by_path import get_function_by_path
from jazzoo.modules.rules.get_targets import get_targets
from jazzoo.modules.rules.eval import eval
from jazzoo.runtime.utils.test_utils import save_fixture

# ---------------------------------------------------------------------------
# Private imports: `from ./foo.jaz import ... as ns` places functions under an
# alias sub-module. They are private — not targets, not listed by `jaz --list`,
# and not visible to modules that import this module.
# ---------------------------------------------------------------------------

# A library module used as the import source. It exports two functions, defines
# a 🐭 (module) var and a 🐐 (global) var, and privately imports something of its
# own to exercise import-* non-transitivity.
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
# NOT leak through `from ./foo.jaz import * as ns`.
save_fixture("""# helper.jaz
secret():
    #!/usr/bin/env bash
    echo "secret"
""")

# A module whose function reads 🐐 to prove globals are shared across modules.
save_fixture("""# glob.jaz
touch():
    #!/usr/bin/env bash
    echo 🐐.shared
""")


def test_single_import():
    jazzoo_fn = save_fixture("""# test_single_import.jaz
    from ./foo.jaz import bar as baz
    """)
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
    jazzoo_fn = save_fixture("""# test_import_tuple.jaz
    from ./foo.jaz import (bar, okay) as baz
    """)
    root_module = parse_module(jazzoo_fn)

    # Both symbols placed under the shared alias sub-module.
    assert get_function_by_path(root_module, "baz.bar") is not None
    assert get_function_by_path(root_module, "baz.okay") is not None

    # Still private — nothing listed at root.
    assert get_targets(root_module) == []


def test_import_symbol_alias():
    jazzoo_fn = save_fixture("""# test_import_symbol_alias.jaz
    from ./foo.jaz import (bar as hello, okay) as baz
    """)
    root_module = parse_module(jazzoo_fn)

    # `bar as hello` → reachable as hello, original name gone.
    assert get_function_by_path(root_module, "baz.hello") is not None
    assert get_function_by_path(root_module, "baz.bar") is None
    # Non-aliased sibling keeps its name.
    assert get_function_by_path(root_module, "baz.okay") is not None


def test_import_star():
    jazzoo_fn = save_fixture("""# test_import_star.jaz
    from ./foo.jaz import * as foo
    """)
    root_module = parse_module(jazzoo_fn)

    # All of foo's exported functions land under the alias sub-module.
    assert get_function_by_path(root_module, "foo.bar") is not None
    assert get_function_by_path(root_module, "foo.okay") is not None
    # A privately-imported symbol of foo (_h.secret) is NOT re-exported by *.
    assert get_function_by_path(root_module, "foo.secret") is None
    assert get_targets(root_module) == []


# --- Scoping across the import boundary ------------------------------------

def test_mouse_resolves_against_definer():
    # Caller defines its own 🐭.test; the imported bar() must still resolve
    # 🐭.test against foo.jaz, not against the caller.
    jazzoo_fn = save_fixture("""# test_mouse_resolves_against_definer.jaz
    🐭.test = "caller"

    from ./foo.jaz import bar as baz
    """)
    root_module = parse_module(jazzoo_fn)
    foo_module = get_child_module_by_name(root_module, "baz")

    # Same-named 🐭.test in both scopes; each resolves independently.
    assert eval(root_module, "🐭.test") == "caller"
    assert eval(foo_module, "🐭.test") == "mouse"


def test_global_shared_across_modules():
    jazzoo_fn = save_fixture("""# test_global_shared.jaz
    🐐.shared = "from-root"

    from ./glob.jaz import touch as g
    """)
    root_module = parse_module(jazzoo_fn)
    glob_module = get_child_module_by_name(root_module, "g")

    # 🐐 set in the root is visible from the imported module's scope.
    assert eval(root_module, "🐐.shared") == "from-root"
    assert eval(glob_module, "🐐.shared") == "from-root"
