from jazzoo.modules.rules.parse_module import parse_module
from jazzoo.modules.rules.eval import eval
from jazzoo.runtime.utils.test_utils import save_fixture

# A library module of small string helpers, used as pipe stages.
save_fixture("""# helpers.jaz
make-full-path(input, style="posix"):
    #!/usr/bin/env bash
    echo "/data/🐆.style/🐆.input"

drop-config-dir-part(path):
    #!/usr/bin/env bash
    echo "🐆.path" | sed 's|/config||'

clean_up(name, max_length="10", suffix=""):
    #!/usr/bin/env bash
    echo "🐆.name🐆.suffix" | cut -c1-🐆.max_length
""")


def test_currying_binds_a_parameter():
    """Square brackets create a curried function in which the named parameter is
    bound, so the caller may no longer supply an argument for it."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_curry_binds.jaz
        from ./helpers.jaz import make-full-path as h

        🐭.build-windows = 🐭.h.make-full-path[style="windows"]

        go():
            🐆.retval = 🐭.build-windows(input="input.json")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert eval(root_module, "🐭.go()") == "/data/windows/input.json"


def test_currying_leaves_other_parameters_open():
    """Parameters that are not bound by the curry expression are still supplied by
    the caller."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_curry_open.jaz
        from ./helpers.jaz import make-full-path as h

        🐭.build = 🐭.h.make-full-path[style="linux"]

        go():
            🐆.retval = 🐭.build(input="a.json")

        go2():
            🐆.retval = 🐭.build(input="b.json")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert eval(root_module, "🐭.go()") == "/data/linux/a.json"
        assert eval(root_module, "🐭.go2()") == "/data/linux/b.json"


def test_empty_brackets_are_the_function_itself():
    """`f[]` binds no parameters and is equivalent to the bare function symbol.
    `f()` is different - it calls the function."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_empty_brackets.jaz
        from ./helpers.jaz import make-full-path as h

        🐭.a = 🐭.h.make-full-path[]
        🐭.b = 🐭.h.make-full-path

        go():
            🐆.retval = 🐭.a(input="x.json")

        go2():
            🐆.retval = 🐭.b(input="x.json")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert eval(root_module, "🐭.go()") == "/data/posix/x.json"
        assert eval(root_module, "🐭.go2()") == "/data/posix/x.json"


def test_bare_name_marks_a_parameter_as_unbound():
    """A bare parameter name inside the brackets marks it as explicitly unbound;
    every other parameter is bound in the curry expression or by its default."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_bare_name.jaz
        from ./helpers.jaz import clean_up as h

        🐭.shorten = 🐭.h.clean_up[name, max_length="3"]

        go():
            🐆.retval = 🐭.shorten(name="maarten")
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # max_length is bound to 3, suffix falls back to its default, name is open.
        assert eval(root_module, "🐭.go()") == "maa"


def test_pipe_feeds_the_unbound_parameter():
    """The piped value becomes the argument for the stage's single unbound
    parameter."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_pipe_single.jaz
        from ./helpers.jaz import make-full-path as h

        go():
            🐆.retval = "input.json" | 🐭.h.make-full-path[style="linux"]
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert eval(root_module, "🐭.go()") == "/data/linux/input.json"


def test_pipe_without_brackets():
    """A stage piped without brackets is the same as `f[]`, so it must declare
    exactly one parameter in total - otherwise the free one is ambiguous."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_pipe_no_brackets.jaz
        from ./helpers.jaz import drop-config-dir-part as h

        go():
            🐆.retval = "/data/config/input.json" | 🐭.h.drop-config-dir-part
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert eval(root_module, "🐭.go()") == "/data/input.json"


def test_the_free_parameter_must_be_unambiguous():
    """A function with more than one parameter must say which parameter is free,
    even when the others all have defaults. Naming it bare and binding everything
    else are equivalent."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_free_param.jaz
        from ./helpers.jaz import make-full-path as h

        by-naming-the-free-one():
            🐆.retval = "input.json" | 🐭.h.make-full-path[input]

        by-binding-the-rest():
            🐆.retval = "input.json" | 🐭.h.make-full-path[style="posix"]
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # `input` is free and takes the piped value; `style` falls back to its default.
        assert eval(root_module, "🐭.by-naming-the-free-one()") == "/data/posix/input.json"
        assert eval(root_module, "🐭.by-binding-the-rest()") == "/data/posix/input.json"


def test_pipe_chain_passes_return_values_onwards():
    """Each stage's return value is piped onwards to the next stage."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_pipe_chain.jaz
        from ./helpers.jaz import * as h

        go():
            🐆.retval = "input.json" \\
                | 🐭.h.make-full-path[style="config"] \\
                | 🐭.h.drop-config-dir-part \\
                | 🐭.h.clean_up[name, max_length="7"]
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # "input.json" -> "/data/config/input.json" -> "/data/input.json" -> "/data/i"
        assert eval(root_module, "🐭.go()") == "/data/i"


def test_pipe_applies_to_builtin_functions():
    """Built-in ⚙️ functions are piped exactly like user functions."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_pipe_builtin.jaz
        go():
            🐆.retval = "/data/sub/../input.json" | ⚙️.abs

        go2():
            🐆.retval = "/data/input.json" | ⚙️.basename | ⚙️.stem
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert eval(root_module, "🐭.go()") == "/data/input.json"
        assert eval(root_module, "🐭.go2()") == "input"
