"""Export layers: `from ./x.jaz export (a,) as ns` (design sections 9 and 10).

A layer groups exported targets under a name reachable from the CLI as a dotted
path (`jaz ns.a`). Layers are an export-side surface only: a .jaz file can refer to
imported symbols, never to a layer, which is why a layer alias and an import alias
may share a name.
"""

import pytest

from jazzoo import ParseError, get_targets, parse_module
from jazzoo.runtime.entrypoints.jazzoo import main
from jazzoo.runtime.utils.test_utils import save_fixture

# The library the layer tests export from.
save_fixture(
    """# lib.jaz
build(mode="release"):
    @echo "build 🐆.mode"

test():
    @echo "test"
"""
)

# A second library, so a layer can be assembled from more than one file.
save_fixture(
    """# styles.jaz
lint():
    @echo "lint"
"""
)

# A module that itself exports a layer, so layers can be shown to nest.
save_fixture(
    """# nested.jaz
from ./lib.jaz export (build,) as react
"""
)


def test_a_layer_groups_targets_under_a_dotted_path(capsys):
    """An export may name a namespace, which groups the exported functions under a
    layer instead of landing them flat. The target is then named by its dotted
    path."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_layer_basic.jaz
        from ./lib.jaz export (build,) as fe
        """
        )

        # Run
        exit_code = main(["fe.build", "mode=dev", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 0
        assert "build dev" in captured.out

    """A renamed symbol takes its new name inside the layer."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_layer_rename.jaz
        from ./lib.jaz export (build as compile,) as fe
        """
        )

        # Run
        exit_code = main(["fe.compile", "mode=dev", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 0
        assert "build dev" in captured.out


def test_a_layered_export_does_not_land_flat():
    """A layer groups its symbols *instead of* landing them flat, so the bare name
    is not a target of the importing module."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_layer_not_flat.jaz
        from ./lib.jaz export (build,) as fe
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert "build" not in {f.name for f in get_targets(root_module)}


def test_naming_symbols_into_a_layer_requires_the_tuple_form(capsys):
    """A bare symbol before `as` is already the rename form: `export bar as fe`
    exports `bar` under the name `fe`, and keeps that meaning."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_bare_as_is_rename.jaz
        from ./lib.jaz export build as fe
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # `fe` is the renamed function itself, flat - not a layer.
        assert "fe" in {f.name for f in get_targets(root_module)}

        # Run
        exit_code = main(["fe", "mode=dev", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 0
        assert "build dev" in captured.out


def test_a_wildcard_needs_no_tuple(capsys):
    """`export * as fe` needs no tuple, since `*` cannot be renamed and so has only
    one reading."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_layer_wildcard.jaz
        from ./lib.jaz export * as fe
        """
        )

        # Run
        exit_code = main(["fe.test", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 0
        assert "test" in captured.out


def test_layers_nest(capsys):
    """A layer's members are whatever the exported module itself exports, so if that
    module in turn exports a layer, it is reachable through this one. Each file only
    declares its own layer."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_layer_nested.jaz
        from ./nested.jaz export * as fe
        """
        )

        # Run
        exit_code = main(["fe.react.build", "mode=dev", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 0
        assert "build dev" in captured.out


def test_a_layer_can_be_named_in_a_tuple_export(capsys):
    """Layers nest because a layer is itself an exported symbol: a module that
    exports a layer offers it under that name, and an importer may re-export it
    exactly as it would a function."""
    if True:
        # Config
        # nested.jaz exports lib.jaz's `build` as the layer `react`.
        jazzoo_fn = save_fixture(
            """# test_named_layer.jaz
        from ./nested.jaz export (react,) as fe
        """
        )

        # Run
        exit_code = main(["fe.react.build", "mode=dev", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 0
        assert "build dev" in captured.out

    """Naming a layer selects it whole, so it also shows up in a listing."""
    if True:
        # Run
        exit_code = main(["--list-all", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 0
        assert "fe.react.build" in captured.out


def test_a_named_layer_can_be_renamed(capsys):
    """A layer may be renamed like any other symbol, which renames the path
    segment."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_renamed_layer.jaz
        from ./nested.jaz export (react as r,) as fe
        """
        )

        # Run
        exit_code = main(["fe.r.build", "mode=dev", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 0
        assert "build dev" in captured.out


def test_exporting_a_function_and_a_layer_under_one_name_is_an_error():
    """Because a layer and a function are both symbols, a module may not export both
    under one name."""
    if True:
        # Config
        # `react` is both a layer and a re-exported function in the same module.
        save_fixture(
            """# clash.jaz
        from ./lib.jaz export (build,) as react
        from ./lib.jaz export (test as react,)
        """
        )
        jazzoo_fn = save_fixture(
            """# test_layer_function_clash.jaz
        from ./clash.jaz export * as fe
        """
        )

        # Run / Assert
        with pytest.raises(ParseError):
            parse_module(jazzoo_fn)


def test_exporting_into_the_same_layer_aggregates(capsys):
    """Exporting into the same layer more than once aggregates, so a layer can be
    assembled from several files."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_layer_aggregate.jaz
        from ./lib.jaz export (build,) as fe
        from ./styles.jaz export (lint,) as fe
        """
        )

        # Run
        build_code = main(["fe.build", "mode=dev", "--file", jazzoo_fn])
        build_out = capsys.readouterr().out
        lint_code = main(["fe.lint", "--file", jazzoo_fn])
        lint_out = capsys.readouterr().out

        # Assert
        assert build_code == 0 and "build dev" in build_out
        assert lint_code == 0 and "lint" in lint_out


def test_a_collision_within_one_layer_is_an_error():
    """Two exports landing different functions under the same name in one layer is
    a ParseError, attributed to the second statement."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_layer_collision.jaz
        from ./lib.jaz export (build,) as fe
        from ./styles.jaz export (lint as build,) as fe
        """
        )

        # Run / Assert
        with pytest.raises(ParseError) as error:
            parse_module(jazzoo_fn)

        # Attributed to the second declaration, which is the one to remove.
        assert error.value.line == 2


def test_the_same_function_exported_into_a_layer_twice_is_one_target(capsys):
    """When both exports trace back to the same function definition - directly or
    through a module that re-exports it - they are one target, not a collision."""
    if True:
        # Config
        save_fixture(
            """# relay.jaz
        from ./lib.jaz export build
        """
        )
        jazzoo_fn = save_fixture(
            """# test_layer_same_function.jaz
        from ./lib.jaz export (build,) as fe
        from ./relay.jaz export (build,) as fe
        from ./lib.jaz export (build,) as fe
        """
        )

        # Run
        list_code = main(["--list", "fe", "--file", jazzoo_fn])
        listing = capsys.readouterr().out.splitlines()
        build_code = main(["fe.build", "mode=dev", "--file", jazzoo_fn])
        build_out = capsys.readouterr().out

        # Assert
        assert list_code == 0
        assert listing.count("fe.build") == 1
        assert build_code == 0 and "build dev" in build_out


def test_a_layer_alias_and_an_import_alias_are_separate(capsys):
    """The same name may be used for an import namespace and an export layer. They
    populate two different surfaces and do not collide."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_layer_and_import.jaz
        from ./lib.jaz import (build,) as fe
        from ./lib.jaz export (test,) as fe

        local():
            🐭.fe.build(mode="dev")
        """
        )

        # Run
        # The import surface: 🐭.fe.build() resolves to the imported function.
        local_code = main(["local", "--file", jazzoo_fn])
        local_out = capsys.readouterr().out
        # The export surface: jaz fe.test reaches the exported one.
        test_code = main(["fe.test", "--file", jazzoo_fn])
        test_out = capsys.readouterr().out

        # Assert
        assert local_code == 0 and "build dev" in local_out
        assert test_code == 0 and "test" in test_out


def test_an_import_namespace_is_not_reachable_from_the_cli(capsys):
    """The path is resolved against export layers only, so a name that exists solely
    as an import is `no such target`."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_import_not_cli.jaz
        from ./lib.jaz import (build,) as fe
        """
        )

        # Run
        exit_code = main(["fe.build", "mode=dev", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 1
        assert "no such target: fe.build" in captured.err


def test_list_shows_a_layer_as_a_single_entry(capsys):
    """`jaz --list` lists the root file's targets. An export layer appears as a
    single entry marked as a layer rather than being expanded."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_list_layer.jaz
        from ./lib.jaz export (build,) as fe

        own():
            @echo "own"
        """
        )

        # Run
        exit_code = main(["--list", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 0
        assert "own" in captured.out
        assert "fe..." in captured.out
        # Not expanded: the members are not listed at this level.
        assert "fe.build" not in captured.out


def test_list_of_a_layer_shows_its_members(capsys):
    """`jaz --list <path>` describes what is at that path. For a layer, that is its
    members - again one level deep."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_list_members.jaz
        from ./lib.jaz export (build, test) as fe
        from ./nested.jaz export * as fe
        """
        )

        # Run
        exit_code = main(["--list", "fe", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 0
        assert "fe.build" in captured.out
        assert "fe.test" in captured.out
        # A nested layer is itself shown as a layer, not expanded.
        assert "fe.react..." in captured.out
        assert "fe.react.build" not in captured.out


def test_list_of_a_target_shows_its_signature(capsys):
    """For a target, `--list <path>` shows the signature, which is how a caller
    finds out what arguments it takes."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_list_signature.jaz
        from ./lib.jaz export (build,) as fe
        """
        )

        # Run
        exit_code = main(["--list", "fe.build", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 0
        assert 'fe.build(mode="release")' in captured.out


def test_list_all_walks_the_whole_tree(capsys):
    """`jaz --list-all` walks the whole tree and lists every target at every
    depth."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_list_all.jaz
        from ./nested.jaz export * as fe

        own():
            @echo "own"
        """
        )

        # Run
        exit_code = main(["--list-all", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 0
        assert "own" in captured.out
        assert "fe.react.build" in captured.out


def test_list_all_distinguishes_two_layers_from_one_file(capsys):
    """Two layers may be bound from the same .jaz file. They are different bindings,
    so both are walked - only a layer that genuinely repeats is skipped."""
    if True:
        # Config
        # `fe` and `fe.inner` both trace back to lib.jaz, but are distinct layers.
        save_fixture(
            """# middle.jaz
        from ./lib.jaz export (test,) as inner
        """
        )
        jazzoo_fn = save_fixture(
            """# test_list_all_same_file.jaz
        from ./lib.jaz export (build,) as fe
        from ./middle.jaz export * as fe
        """
        )

        # Run
        exit_code = main(["--list-all", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 0
        assert "fe.build" in captured.out
        # The nested layer shares lib.jaz with `fe`, but is still its own binding.
        assert "fe.inner.test" in captured.out


def test_list_all_terminates_on_a_circular_import(capsys):
    """Because circular imports are allowed, the walk tracks the modules it has
    already entered. A layer whose module has already been entered is skipped, so
    --list-all always terminates and never prints the same target twice."""
    if True:
        # Config
        # cycle_a exports cycle_b as a layer, and cycle_b exports cycle_a back.
        save_fixture(
            """# cycle_a.jaz
        from ./cycle_b.jaz export * as b

        a_target():
            @echo "a"
        """
        )
        save_fixture(
            """# cycle_b.jaz
        from ./cycle_a.jaz export * as a

        b_target():
            @echo "b"
        """
        )
        jazzoo_fn = save_fixture(
            """# test_list_all_cycle.jaz
        from ./cycle_a.jaz export * as root
        """
        )

        # Run
        exit_code = main(["--list-all", "--file", jazzoo_fn])
        captured = capsys.readouterr()

        # Assert
        assert exit_code == 0
        # It terminated, and each target appears exactly once.
        assert captured.out.count("root.a_target") == 1
        assert captured.out.count("root.b.b_target") == 1
