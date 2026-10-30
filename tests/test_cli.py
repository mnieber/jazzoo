"""The `jaz` command-line interface.

Most tests here name the .jaz file explicitly with `--file`, so a fixture can keep
a descriptive filename. The discovery tests instead chdir into the fixture dir and
rely on the documented default-file rules.
"""

import os

from jazzoo import ArgumentError
from jazzoo.runtime.entrypoints.jazzoo import main
from jazzoo.runtime.utils.test_utils import save_fixture


def test_a_target_runs_with_named_arguments(capsys):
    """`jaz <target> [arg=value ...]` runs a target. Arguments are always named."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_run_target.jaz
        debug(name="me"):
            echo "Running debug for: 🐆.name"
        """
        )

        # Run
        exit_code = main(["debug", "name=jane", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 0
        assert "Running debug for: jane" in captured.out

    """A parameter with a default may be omitted."""
    if True:
        # Run
        exit_code = main(["debug", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 0
        assert "Running debug for: me" in captured.out


def test_several_named_arguments_are_passed_in_any_order(capsys):
    """Named arguments identify their parameter, so their order does not matter."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_named_order.jaz
        build(target, mode="release"):
            echo "🐆.target/🐆.mode"
        """
        )

        # Run
        in_order = main(["build", "target=myapp", "mode=debug", "--file", jazzoo_fn])
        first = capsys.readouterr()

        reversed_order = main(
            ["build", "mode=debug", "target=myapp", "--file", jazzoo_fn]
        )
        second = capsys.readouterr()

        # Assert
        assert in_order == 0
        assert reversed_order == 0
        assert "myapp/debug" in first.out
        assert "myapp/debug" in second.out


def test_the_first_parameter_may_be_passed_positionally(capsys):
    """As a convenience, an argument for the first declared parameter of a target may
    be passed positionally at the CLI."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_positional_shorthand.jaz
        build(target, mode="release"):
            echo "🐆.target/🐆.mode"
        """
        )

        # Run
        positional = main(["build", "myapp", "--file", jazzoo_fn])
        from_positional = capsys.readouterr()

        named = main(["build", "target=myapp", "--file", jazzoo_fn])
        from_named = capsys.readouterr()

        # Assert
        # `jaz build myapp` is equivalent to `jaz build target=myapp`.
        assert positional == 0
        assert named == 0
        assert from_positional.out == from_named.out

    """The positional argument may be mixed with named arguments for the rest."""
    if True:
        # Run
        exit_code = main(["build", "myapp", "mode=debug", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 0
        assert "myapp/debug" in captured.out


def test_passing_an_argument_twice_is_an_error(capsys):
    """Passing the same argument both positionally and by name is an error."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_duplicate_argument.jaz
        build(target, mode="release"):
            echo "🐆.target/🐆.mode"
        """
        )

        # Run
        exit_code = main(["build", "myapp", "target=other", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code != 0
        assert "target" in captured.err


def test_a_positional_argument_must_come_first(capsys):
    """If mixing positional and named, the positional argument must come first."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_positional_first.jaz
        build(target, mode="release"):
            echo "🐆.target/🐆.mode"
        """
        )

        # Run
        exit_code = main(["build", "mode=debug", "myapp", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code != 0
        assert captured.err


def test_the_positional_shorthand_is_cli_only():
    """Within .jaz files all arguments must be named - the positional shorthand is
    CLI-only."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_shorthand_is_cli_only.jaz
        build(target, mode="release"):
            echo "🐆.target/🐆.mode"

        test():
            🐭.build("myapp")
        """
        )

        # Run / Assert
        # The same shorthand that works at the CLI is an ArgumentError in a .jaz file.
        try:
            main(["test", "--file", jazzoo_fn])
        except ArgumentError:
            pass


def test_list_shows_the_targets(capsys):
    """`jaz --list` lists available targets."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_list.jaz
        [private]
        _helper():
            echo "helper"

        build():
            echo "build"

        deploy():
            echo "deploy"
        """
        )

        # Run
        exit_code = main(["--list", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 0
        assert "build" in captured.out
        assert "deploy" in captured.out
        # [private] functions are not targets, so they are not listed.
        assert "_helper" not in captured.out


def test_imported_targets_are_not_listed_but_exported_ones_are(capsys):
    """Imported functions are private and do not appear in `jaz --list`; exported
    ones land flat in 🐭 and become targets."""
    if True:
        # Config
        save_fixture(
            """# library.jaz
        imported-target():
            echo "imported"

        exported-target():
            echo "exported"
        """
        )

        jazzoo_fn = save_fixture(
            """# test_list_imports.jaz
        from ./library.jaz import imported-target as ns
        from ./library.jaz export exported-target

        own-target():
            echo "own"
        """
        )

        # Run
        exit_code = main(["--list", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 0
        assert "own-target" in captured.out
        assert "exported-target" in captured.out
        assert "imported-target" not in captured.out


def test_a_private_function_cannot_be_invoked_from_the_cli(capsys):
    """[private] functions are not targets and cannot be invoked from the CLI, even
    though they are callable from within .jaz files."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_private_not_invokable.jaz
        [private]
        _helper():
            echo "helper ran"

        build():
            🐭._helper()
        """
        )

        # Run
        direct = main(["_helper", "--file", jazzoo_fn])
        direct_output = capsys.readouterr()

        via_target = main(["build", "--file", jazzoo_fn])
        via_target_output = capsys.readouterr()

        # Assert
        assert direct != 0
        assert "helper ran" not in direct_output.out
        # The same function is reachable from inside the file.
        assert via_target == 0
        assert "helper ran" in via_target_output.out


def test_running_jaz_with_no_arguments_lists_the_targets(capsys):
    """Running `jaz` with no arguments lists available targets."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_no_arguments.jaz
        build():
            echo "build"

        deploy():
            echo "deploy"
        """
        )

        # Run
        bare = main(["--file", jazzoo_fn])
        bare_output = capsys.readouterr()

        listed = main(["--list", "--file", jazzoo_fn])
        listed_output = capsys.readouterr()

        # Assert
        assert bare == 0
        assert listed == 0
        assert bare_output.out == listed_output.out


def test_an_unknown_target_is_an_error(capsys):
    """Naming a target that does not exist fails rather than doing nothing."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_unknown_target.jaz
        build():
            echo "build"
        """
        )

        # Run
        exit_code = main(["no-such-target", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code != 0
        assert "no-such-target" in captured.err


def test_the_default_file_is_jazzoo_in_the_current_directory(capsys, monkeypatch):
    """The default file is `jazzoo` (no extension) in the current directory."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# jazzoo
        build():
            echo "from the default file"
        """
        )

        # Run
        monkeypatch.chdir(os.path.dirname(jazzoo_fn))
        exit_code = main(["build"])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 0
        assert "from the default file" in captured.out


def test_the_default_file_falls_back_to_jazzoo_jaz(capsys, monkeypatch, tmp_path):
    """The default file falls back to `jazzoo.jaz` if `jazzoo` is not found."""
    if True:
        # Config
        # A directory of its own, so the `jazzoo` file saved by the test above is
        # not the one that gets discovered.
        fallback_dir = tmp_path / "fallback"
        fallback_dir.mkdir()
        (fallback_dir / "jazzoo.jaz").write_text(
            'build():\n    echo "from the fallback file"\n', encoding="utf-8"
        )

        # Run
        monkeypatch.chdir(fallback_dir)
        exit_code = main(["build"])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 0
        assert "from the fallback file" in captured.out

    """`jazzoo` wins when both are present."""
    if True:
        # Config
        (fallback_dir / "jazzoo").write_text(
            'build():\n    echo "from the preferred file"\n', encoding="utf-8"
        )

        # Run
        exit_code = main(["build"])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 0
        assert "from the preferred file" in captured.out


def test_root_module_system_variables_name_the_entry_point(capsys, monkeypatch):
    """⚙️.root_module.* refers to the entry-point .jaz file invoked by jaz, even when
    the reference is made from an imported module."""
    if True:
        # Config
        save_fixture(
            """# reports_root.jaz
        report():
            echo "root=⚙️.root_module.basename module=⚙️.module.basename"
        """
        )

        jazzoo_fn = save_fixture(
            """# test_root_module.jaz
        from ./reports_root.jaz import report as lib

        go():
            🐭.lib.report()
        """
        )

        # Run
        monkeypatch.chdir(os.path.dirname(jazzoo_fn))
        exit_code = main(["go", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        # The entry point is the file jaz was pointed at; the module is the file the
        # line lives in.
        assert exit_code == 0
        assert "root=test_root_module.jaz" in captured.out
        assert "module=reports_root.jaz" in captured.out
