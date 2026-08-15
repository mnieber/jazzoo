import os
from jazzoo.modules.rules.parse_module import parse_module
from jazzoo.modules.rules.get_child_module_by_name import get_child_module_by_name
from jazzoo.modules.rules.get_module_by_path import get_module_by_path
from jazzoo.modules.rules.get_function_by_path import get_function_by_path
from jazzoo.modules.rules.get_targets import get_targets
from jazzoo.modules.rules.eval import eval
from jazzoo.runtime.utils.test_utils import save_fixture

# A library module used as the import source.
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

# A second-level module that foo.jaz privately imports from.
save_fixture("""# helper.jaz
secret():
    #!/usr/bin/env bash
    echo "secret"
""")


def test_single_import():
    """Importing a module implies that the module and global symbols - defined in that module -
    become available."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_single_import.jaz
        from ./foo.jaz import bar as baz
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        baz_module = get_child_module_by_name(root_module, "baz")
        fn = get_function_by_path(root_module, "baz.bar")

        # Assert

        assert baz_module.filename == os.path.join(
            os.path.dirname(jazzoo_fn), "foo.jaz"
        )
        assert eval(root_module, "🐐.test") == "123"
        assert eval(baz_module, "🐭.test") == "mouse"
        assert fn.is_target is False
        assert get_targets(root_module) == []


def test_import_tuple_and_assign_alias():
    """You can import a function from a module into an alias sub-module, and assign an alias."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_import_tuple_and_assign_alias.jaz
        from ./foo.jaz import (bar as hello, okay) as baz
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert get_function_by_path(root_module, "baz.hello") is not None
        assert get_function_by_path(root_module, "baz.bar") is None
        assert get_function_by_path(root_module, "baz.okay") is not None


def test_import_star():
    """Import star imports all targets."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_import_star.jaz
        from ./foo.jaz import * as foo
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert get_function_by_path(root_module, "foo.bar") is not None
        assert get_function_by_path(root_module, "foo.okay") is not None
        assert get_function_by_path(root_module, "foo.secret") is None
        assert get_targets(root_module) == []


def test_resolve_module_symbols():
    """Symbols defined in the module scope are resolved against the module scope."""
    if True:
        # Config
        # Caller defines its own 🐭.test; the imported bar() must still resolve
        # 🐭.test against foo.jaz, not against the caller.
        root_module_fn = save_fixture("""# test_resolve_module_symbols.jaz
        🐭.test = "caller"

        from ./foo.jaz import bar as baz
        """)
        root_module = parse_module(root_module_fn)
        foo_module = get_child_module_by_name(root_module, "baz")

        # Same-named 🐭.test in both scopes; each resolves independently.
        assert eval(root_module, "🐭.test") == "caller"
        assert eval(foo_module, "🐭.test") == "mouse"


def test_global_symbols_are_shared_across_modules():
    if True:
        # Config
        save_fixture("""# glob.jaz
        touch():
            #!/usr/bin/env bash
            echo 🐐.shared
        """)

        jazzoo_fn = save_fixture("""# test_global_shared.jaz
        🐐.shared = "from-root"

        from ./glob.jaz import touch as g
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        glob_module = get_child_module_by_name(root_module, "g")

        # Assert
        assert eval(root_module, "🐐.shared") == "from-root"
        assert eval(root_module, "🐭.g()") == "from-root"
        assert eval(glob_module, "🐐.shared") == "from-root"
        assert eval(glob_module, "🐭.touch()") == "from-root"


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
