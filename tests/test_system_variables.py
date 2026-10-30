"""The built-in ⚙️ namespace.

⚙️.stdout and ⚙️.output are covered in test_shebang_blocks.py, since their values
follow from how blocks execute. ⚙️.env is covered in test_substitutions.py, and the
path operators (⚙️.abs, ⚙️.basename, ...) in test_expressions.py. What is left here
are the module and root_module variables, which are constant for a whole run.
"""

import os

import pytest

from jazzoo import ResolutionError, evaluate, parse_module
from jazzoo.runtime.utils.test_utils import save_fixture


def test_the_module_variables_describe_the_current_file():
    """⚙️.module.basename, .path and .dirname describe the current module file."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_module_vars.jaz
        basename():
            echo "⚙️.module.basename"

        path():
            echo "⚙️.module.path"

        dirname():
            echo "⚙️.module.dirname"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.basename()") == "test_module_vars.jaz"
        assert evaluate(root_module, "🐭.path()") == jazzoo_fn
        assert evaluate(root_module, "🐭.dirname()") == os.path.dirname(jazzoo_fn)


def test_the_module_path_is_absolute():
    """⚙️.module.path is an absolute path, and .dirname is the absolute path of the
    directory containing it."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_module_path_absolute.jaz
        go():
            echo "⚙️.module.path|⚙️.module.dirname"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)
        path, dirname = evaluate(root_module, "🐭.go()").split("|")

        # Assert
        assert os.path.isabs(path)
        assert os.path.isabs(dirname)
        # The three module variables agree with each other.
        assert os.path.join(dirname, "test_module_path_absolute.jaz") == path


def test_the_module_variables_are_per_module():
    """⚙️.module refers to the file the line lives in, so an imported module reports
    itself rather than the file that imported it."""
    if True:
        # Config
        library_fn = save_fixture(
            """# module_vars_library.jaz
        report():
            echo "⚙️.module.basename"
        """
        )

        jazzoo_fn = save_fixture(
            """# test_module_vars_per_module.jaz
        from ./module_vars_library.jaz import report as lib

        from-the-library():
            🐆.retval = 🐭.lib.report()

        from-here():
            echo "⚙️.module.basename"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert (
            evaluate(root_module, "🐭.from-the-library()") == "module_vars_library.jaz"
        )
        assert (
            evaluate(root_module, "🐭.from-here()") == "test_module_vars_per_module.jaz"
        )
        # The two files really are different files.
        assert library_fn != jazzoo_fn


def test_the_root_module_variables_describe_the_entry_point():
    """⚙️.root_module.basename, .path and .dirname describe the entry-point .jaz file
    invoked by jaz."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_root_module_vars.jaz
        basename():
            echo "⚙️.root_module.basename"

        path():
            echo "⚙️.root_module.path"

        dirname():
            echo "⚙️.root_module.dirname"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.basename()") == "test_root_module_vars.jaz"
        assert evaluate(root_module, "🐭.path()") == jazzoo_fn
        assert evaluate(root_module, "🐭.dirname()") == os.path.dirname(jazzoo_fn)


def test_the_root_module_variables_are_the_same_in_every_module():
    """⚙️.root_module is the entry point for the whole run, so an imported module
    reports the same values as the file that imported it."""
    if True:
        # Config
        save_fixture(
            """# root_module_library.jaz
        report():
            echo "⚙️.root_module.basename|⚙️.module.basename"
        """
        )

        jazzoo_fn = save_fixture(
            """# test_root_module_shared.jaz
        from ./root_module_library.jaz import report as lib

        go():
            🐆.retval = 🐭.lib.report()
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)
        root_basename, module_basename = evaluate(root_module, "🐭.go()").split("|")

        # Assert
        # The line runs inside the library, but the root module is the entry point.
        assert root_basename == "test_root_module_shared.jaz"
        assert module_basename == "root_module_library.jaz"


def test_the_root_module_variables_agree_with_each_other():
    """.path is absolute, .dirname is its directory, and .basename its filename."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_root_module_agreement.jaz
        go():
            echo "⚙️.root_module.path|⚙️.root_module.dirname|⚙️.root_module.basename"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)
        path, dirname, basename = evaluate(root_module, "🐭.go()").split("|")

        # Assert
        assert os.path.isabs(path)
        assert os.path.isabs(dirname)
        assert os.path.join(dirname, basename) == path


def test_the_system_variables_are_constant_for_a_run():
    """The module and root_module variables are constant for the lifetime of a run,
    unlike ⚙️.stdout and ⚙️.output which jazzoo updates as a body runs."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_system_vars_constant.jaz
        go():
            #!/usr/bin/env bash
            echo "first block"

            #!
            🐆.first = "⚙️.module.basename"
            echo "second block"
            🐆.second = "⚙️.module.basename"
            🐆.retval = "🐆.first/🐆.second"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # Blocks ran in between, but ⚙️.module did not change.
        assert (
            evaluate(root_module, "🐭.go()")
            == "test_system_vars_constant.jaz/test_system_vars_constant.jaz"
        )


def test_system_variables_can_be_used_in_expressions():
    """⚙️ variables are ordinary values: they take part in path joins and pipes."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_system_vars_in_expressions.jaz
        joined():
            🐆.retval = ⚙️.module.dirname / "build/output"

        piped():
            🐆.retval = ⚙️.module.path | ⚙️.basename | ⚙️.stem
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.joined()").endswith("/build/output")
        assert evaluate(root_module, "🐭.piped()") == "test_system_vars_in_expressions"


def test_an_unknown_system_variable_is_a_resolution_error():
    """⚙️ is a fixed set of built-ins, so an unknown name in it does not resolve."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_unknown_system_var.jaz
        go():
            echo "⚙️.module.no-such-part"

        top-level():
            echo "⚙️.no-such-variable"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        with pytest.raises(ResolutionError):
            evaluate(root_module, "🐭.go()")
        with pytest.raises(ResolutionError):
            evaluate(root_module, "🐭.top-level()")
