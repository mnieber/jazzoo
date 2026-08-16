"""Reading and writing a 🐭 variable through imported accessor functions.

The scoping rule is stated twice in the design: "when a function from module B is
called by module A, 🐭 resolves against B's scope, not A's", and "the imported
module's 🐭 variables resolve against the imported file's scope, not the caller's".

The existing import tests only ever *read* 🐭 from an imported function, and the
only tests that *write* 🐭 from a function body have caller and callee in the same
file. A getter/setter pair crosses both at once: the setter mutates the callee's
module scope, and the caller has a same-named 🐭 that must not move.
"""

from jazzoo import evaluate, get_module_by_path, parse_module
from jazzoo.runtime.utils.test_utils import save_fixture


def test_an_imported_setter_writes_the_defining_modules_scope():
    """A setter called from another module writes 🐭 in the file that defines it,
    and a getter from that same file reads the value back."""
    if True:
        # Config
        save_fixture("""# counter.jaz
        🐭.value = "initial"

        set-value(to):
            🐭.value = 🐆.to

        get-value():
            🐆.retval = 🐭.value
        """)

        jazzoo_fn = save_fixture("""# test_accessors.jaz
        from ./counter.jaz import (set-value, get-value) as c

        go():
            🐭.c.set-value(to="42")
            🐆.retval = 🐭.c.get-value()
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # The setter's write is visible to the getter, because both resolve 🐭
        # against counter.jaz.
        assert evaluate(root_module, "🐭.go()") == "42"


def test_an_imported_setter_does_not_touch_the_callers_scope():
    """The caller may hold a 🐭 variable of the same name; the imported setter must
    not write to it."""
    if True:
        # Config
        save_fixture("""# store.jaz
        🐭.value = "callee-initial"

        set-value(to):
            🐭.value = 🐆.to

        get-value():
            🐆.retval = 🐭.value
        """)

        jazzoo_fn = save_fixture("""# test_accessor_isolation.jaz
        🐭.value = "caller-owns-this"

        from ./store.jaz import (set-value, get-value) as s

        go():
            🐭.s.set-value(to="written-by-caller")
            🐆.theirs = 🐭.s.get-value()
            🐆.retval = "theirs=🐆.theirs mine=🐭.value"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # Same name, two scopes: the setter moved the callee's, not the caller's.
        assert (
            evaluate(root_module, "🐭.go()")
            == "theirs=written-by-caller mine=caller-owns-this"
        )


def test_the_write_is_visible_when_the_module_is_inspected_directly():
    """The value the setter wrote lives in the imported module's own scope, so
    evaluating against that module sees it."""
    if True:
        # Config
        save_fixture("""# settings_store.jaz
        🐭.level = "info"

        set-level(to):
            🐭.level = 🐆.to
        """)

        jazzoo_fn = save_fixture("""# test_accessor_module_scope.jaz
        from ./settings_store.jaz import set-level as s

        go():
            🐭.s.set-level(to="debug")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        store = get_module_by_path(root_module, "s")

        # Assert
        assert evaluate(store, "🐭.level") == "info"
        evaluate(root_module, "🐭.go()")
        assert evaluate(store, "🐭.level") == "debug"


def test_two_importers_share_one_copy_of_the_imported_modules_state():
    """Modules are cached by resolved path, so a module imported from two places is
    one module - and a setter called through either alias moves the same value."""
    if True:
        # Config
        save_fixture("""# shared_store.jaz
        🐭.value = "start"

        set-value(to):
            🐭.value = 🐆.to

        get-value():
            🐆.retval = 🐭.value
        """)

        save_fixture("""# writer.jaz
        from ./shared_store.jaz import set-value as store

        write():
            🐭.store.set-value(to="written")
        """)

        jazzoo_fn = save_fixture("""# test_accessor_shared.jaz
        from ./shared_store.jaz import get-value as store
        from ./writer.jaz import write as w

        go():
            🐭.w.write()
            🐆.retval = 🐭.store.get-value()
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # The write went through writer.jaz's alias; the read comes through this
        # file's own alias. One cached module, so one value.
        assert evaluate(root_module, "🐭.go()") == "written"


def test_a_global_written_by_an_imported_function_is_shared():
    """🐐 contrasts with 🐭: it is truly global, so a setter writing 🐐 is visible
    to the caller under the same name."""
    if True:
        # Config
        save_fixture("""# global_store.jaz
        set-shared(to):
            🐐.shared = 🐆.to
        """)

        jazzoo_fn = save_fixture("""# test_accessor_global.jaz
        from ./global_store.jaz import set-shared as g

        go():
            🐭.g.set-shared(to="from-callee")
            🐆.retval = 🐐.shared
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.go()") == "from-callee"
