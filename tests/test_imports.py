import os

import pytest

from jazzoo import (
    ModuleImportError,
    ParseError,
    evaluate,
    get_function_by_path,
    get_module_by_path,
    get_targets,
    parse_module,
)
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
        baz_module = get_module_by_path(root_module, "baz")
        fn = get_function_by_path(root_module, "baz.bar")

        # Assert

        assert baz_module.filename == os.path.join(
            os.path.dirname(jazzoo_fn), "foo.jaz"
        )
        assert evaluate(root_module, "🐐.test") == "123"
        assert evaluate(baz_module, "🐭.test") == "mouse"
        # `bar` is a target of foo.jaz, but importing it privately does not make it
        # a target of this module - see test_targets_from_imported_modules_are_not_listed.
        assert fn.is_target is True
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
        foo_module = get_module_by_path(root_module, "baz")

        # Same-named 🐭.test in both scopes; each resolves independently.
        assert evaluate(root_module, "🐭.test") == "caller"
        assert evaluate(foo_module, "🐭.test") == "mouse"


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
        glob_module = get_module_by_path(root_module, "g")

        # Assert
        assert evaluate(root_module, "🐐.shared") == "from-root"
        # The alias names the namespace, so the function is 🐭.g.touch(), not 🐭.g().
        assert evaluate(root_module, "🐭.g.touch()") == "from-root"
        assert evaluate(glob_module, "🐐.shared") == "from-root"
        assert evaluate(glob_module, "🐭.touch()") == "from-root"


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


def test_importing_a_missing_file_is_a_module_import_error():
    """An import naming a file that does not exist is a ModuleImportError. Paths are
    always explicit relative or absolute - there is no search path to fall back on."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_missing_file.jaz
        from ./nope.jaz import bar as baz
        """)

        # Run / Assert
        with pytest.raises(ModuleImportError):
            parse_module(jazzoo_fn)


def test_importing_an_unknown_symbol_is_a_module_import_error():
    """An import naming a symbol the imported module does not define is a
    ModuleImportError."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_unknown_symbol.jaz
        from ./foo.jaz import no-such-function as baz
        """)

        # Run / Assert
        with pytest.raises(ModuleImportError):
            parse_module(jazzoo_fn)


def test_importing_a_privately_imported_symbol_is_a_module_import_error():
    """Imported functions are private - not visible to outside importers. Naming one
    explicitly is a ModuleImportError, just as `import *` does not pull it in."""
    if True:
        # Config
        # foo.jaz privately imports `secret` from helper.jaz, so `secret` is not a
        # symbol foo.jaz offers to its own importers.
        jazzoo_fn = save_fixture("""# test_private_symbol.jaz
        from ./foo.jaz import secret as baz
        """)

        # Run / Assert
        with pytest.raises(ModuleImportError):
            parse_module(jazzoo_fn)


def test_call_time_circular_imports_are_safe():
    """Circular imports are allowed. Modules are cached by resolved file path after
    first load, and circular references used only at call time are safe."""
    if True:
        # Config
        save_fixture("""# ping.jaz
        from ./pong.jaz import pong as p

        ping():
            🐆.retval = "ping/🐭.p.pong()"
        """)

        save_fixture("""# pong.jaz
        from ./ping.jaz import ping as p

        pong():
            #!/usr/bin/env bash
            echo "pong"
        """)

        jazzoo_fn = save_fixture("""# test_circular_call_time.jaz
        from ./ping.jaz import ping as entry

        go():
            🐆.retval = 🐭.entry.ping()
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # The cycle is only traversed when the call runs, so loading succeeds.
        assert evaluate(root_module, "🐭.go()") == "ping/pong"


def test_load_time_circular_imports_are_a_module_import_error():
    """A circular import receives the cached, partially-initialized module. A
    load-time circular reference - a module-level assignment calling into a module
    that is not yet fully initialized - is a ModuleImportError."""
    if True:
        # Config
        # left.jaz needs a value from right.jaz while right.jaz is still loading.
        save_fixture("""# left.jaz
        from ./right.jaz import value as r

        🐭.eager = 🐭.r.value()

        value():
            #!/usr/bin/env bash
            echo "left"
        """)

        save_fixture("""# right.jaz
        from ./left.jaz import value as l

        🐭.eager = 🐭.l.value()

        value():
            #!/usr/bin/env bash
            echo "right"
        """)

        jazzoo_fn = save_fixture("""# test_circular_load_time.jaz
        from ./left.jaz import value as entry
        """)

        # Run / Assert
        with pytest.raises(ModuleImportError):
            parse_module(jazzoo_fn)


def test_the_same_function_imported_into_a_namespace_twice_is_one_function():
    """Importing the same function definition into one namespace twice - here once
    directly and once through a module that re-exports it - binds it once."""
    if True:
        # Config
        save_fixture("""# relay_foo.jaz
        from ./foo.jaz export bar
        """)
        jazzoo_fn = save_fixture("""# test_import_same_twice.jaz
        from ./foo.jaz import bar as ns
        from ./relay_foo.jaz import bar as ns
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        ns_module = get_module_by_path(root_module, "ns")

        # Assert
        assert [f.name for f in ns_module.functions] == ["bar"]
        assert evaluate(root_module, "🐭.ns.bar()") == "mouse"


def test_different_functions_imported_under_one_name_collide():
    """Two different functions bound under one name in a namespace is a ParseError,
    attributed to the second import - rather than the first one silently winning."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_import_name_clash.jaz
        from ./foo.jaz import okay as ns
        from ./helper.jaz import (secret as okay,) as ns
        """)

        # Run / Assert
        with pytest.raises(ParseError) as error:
            parse_module(jazzoo_fn)

        assert error.value.filename == jazzoo_fn
        assert error.value.line == 2
