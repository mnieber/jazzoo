"""Variables holding JSON values: objects, arrays, numbers, booleans and null.

Covers design section 3 - structured values, dotted paths, the scalar-bare /
container-JSON rendering split, ⚙️.parse and ⚙️.json, and the truthiness rule that
extends beyond strings.

The rendering split is what keeps this backward-compatible: a string leaf renders
bare, so a variable holding a string behaves exactly as it did before structured
values existed. Only containers render as JSON.
"""

import pytest

from jazzoo import ExecutionError, ResolutionError, evaluate, parse_module
from jazzoo.runtime.utils.test_utils import save_fixture


def test_a_dotted_path_reaches_into_an_object():
    """A variable can hold an object, and a dotted name reaches inside it."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_object_access.jaz
        build():
            🐆.config.name = "jane"
            🐆.config.port = 8080
            🐆.retval = "🐆.config.name/🐆.config.port"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.build()") == "jane/8080"


def test_assigning_a_path_creates_the_intermediate_objects():
    """Assigning to a path auto-creates the objects along it, so the container need
    not be declared first."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_autovivify.jaz
        build():
            🐆.config.database.host = "localhost"
            🐆.retval = 🐆.config.database.host
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.build()") == "localhost"


def test_a_path_works_in_every_namespace():
    """🐐, 🐭 and 🐆 all hold structured values."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_paths_all_sigils.jaz
        🐐.global-config.env = "prod"
        🐭.module-config.name = "jazzoo"

        build():
            🐆.local-config.mode = "debug"
            🐆.retval = "🐐.global-config.env/🐭.module-config.name/🐆.local-config.mode"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.build()") == "prod/jazzoo/debug"


def test_an_array_is_indexed_by_a_path_segment():
    """Array elements are reached by index, written as an ordinary path segment."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_array_index.jaz
        build():
            🐆.hosts = ["a.example.com", "b.example.com"]
            🐆.retval = "🐆.hosts.0 and 🐆.hosts.1"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert (
            evaluate(root_module, "🐭.build()")
            == "a.example.com and b.example.com"
        )


def test_a_missing_path_is_a_resolution_error():
    """A path that does not exist is unresolvable, exactly like an unset variable."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_missing_path.jaz
        missing-field():
            🐆.config.name = "jane"
            🐆.retval = 🐆.config.nickname

        missing-index():
            🐆.hosts = ["only-one"]
            🐆.retval = 🐆.hosts.5
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        with pytest.raises(ResolutionError):
            evaluate(root_module, "🐭.missing-field()")
        with pytest.raises(ResolutionError):
            evaluate(root_module, "🐭.missing-index()")


def test_the_markers_apply_to_a_missing_path():
    """`?` and `:-` work on a path like they do on any other reference."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_path_markers.jaz
        optional():
            🐆.config.name = "jane"
            🐆.retval = "[🐆.config.nickname?]"

        with-default():
            🐆.config.name = "jane"
            🐆.retval = 🐆.config.log-level?:-info
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.optional()") == "[]"
        assert evaluate(root_module, "🐭.with-default()") == "info"


def test_a_scalar_renders_bare_and_a_container_renders_as_json():
    """A string leaf renders unquoted; an object or array renders as compact JSON."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_rendering.jaz
        build():
            🐆.config.name = "jane"
            🐆.config.port = 8080
            🐆.retval = "🐆.config.name|🐆.config"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)
        scalar, container = evaluate(root_module, "🐭.build()").split("|")

        # Assert
        # The scalar is bare - this is what keeps a plain string variable behaving
        # exactly as it did before structured values existed.
        assert scalar == "jane"
        # The container is compact JSON, with no spaces.
        assert container == '{"name":"jane","port":8080}'


def test_the_scalar_types_render_as_expected():
    """Numbers render in their JSON form, booleans as true/false, null as empty."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_scalar_rendering.jaz
        build():
            🐆.v.number = 8080
            🐆.v.float = 1.5
            🐆.v.yes = true
            🐆.v.no = false
            🐆.v.nothing = null
            🐆.retval = "[🐆.v.number][🐆.v.float][🐆.v.yes][🐆.v.no][🐆.v.nothing]"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # `null` renders as the empty string, so it splices into a line as nothing.
        assert evaluate(root_module, "🐭.build()") == "[8080][1.5][true][false][]"


def test_a_container_renders_into_a_shell_line():
    """A container rendering is ordinary text, so it can be piped to a JSON tool."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_container_in_shell.jaz
        build():
            🐆.config.name = "jane"
            #!/usr/bin/env bash
            echo '🐆.config'
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.build()") == '{"name":"jane"}'


def test_parse_reads_a_json_string_into_a_value():
    """⚙️.parse turns a command's stdout into a structured value."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_parse.jaz
        [private]
        _load-config():
            #!/usr/bin/env bash
            echo '{"name": "jane", "port": 8080}'

        build():
            🐆.config = 🐭._load-config() | ⚙️.parse
            🐆.retval = "🐆.config.name/🐆.config.port"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.build()") == "jane/8080"


def test_parse_rejects_text_that_is_not_json():
    """⚙️.parse on invalid JSON is an ExecutionError."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_parse_invalid.jaz
        [private]
        _not-json():
            #!/usr/bin/env bash
            echo 'this is not json'

        build():
            🐆.config = 🐭._not-json() | ⚙️.parse
            🐆.retval = "unreachable"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        with pytest.raises(ExecutionError):
            evaluate(root_module, "🐭.build()")


def test_json_renders_a_value_back_to_a_json_string():
    """⚙️.json is the inverse of ⚙️.parse, and unlike plain substitution it quotes a
    string so the result is always valid JSON."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_json_operator.jaz
        a-string():
            🐆.name = "jane"
            🐆.retval = 🐆.name | ⚙️.json

        a-container():
            🐆.config.name = "jane"
            🐆.retval = 🐆.config | ⚙️.json
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # Plain substitution would give `jane`; ⚙️.json keeps it valid JSON.
        assert evaluate(root_module, "🐭.a-string()") == '"jane"'
        assert evaluate(root_module, "🐭.a-container()") == '{"name":"jane"}'


def test_parse_and_json_round_trip():
    """A JSON document survives a trip through jazzoo unchanged."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_round_trip.jaz
        [private]
        _document():
            #!/usr/bin/env bash
            echo '{"name":"jane","port":8080,"tags":["a","b"],"ok":true}'

        build():
            🐆.parsed = 🐭._document() | ⚙️.parse
            🐆.retval = 🐆.parsed | ⚙️.json
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # Numbers are held, not computed with, so 8080 comes back as 8080.
        assert (
            evaluate(root_module, "🐭.build()")
            == '{"name":"jane","port":8080,"tags":["a","b"],"ok":true}'
        )


def test_null_and_empty_containers_are_falsy():
    """Truthiness extends past strings: null, [] and {} are falsy, and so is the
    number 0."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_structured_truthiness.jaz
        nothing():
            🐆.v = null
            🐆.retval = "truthy" if 🐆.v else "falsy"

        empty-array():
            🐆.v = []
            🐆.retval = "truthy" if 🐆.v else "falsy"

        empty-object():
            🐆.v = {}
            🐆.retval = "truthy" if 🐆.v else "falsy"

        zero():
            🐆.v = 0
            🐆.retval = "truthy" if 🐆.v else "falsy"

        boolean-false():
            🐆.v = false
            🐆.retval = "truthy" if 🐆.v else "falsy"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        for target in [
            "nothing",
            "empty-array",
            "empty-object",
            "zero",
            "boolean-false",
        ]:
            assert evaluate(root_module, f"🐭.{target}()") == "falsy"


def test_a_non_empty_container_is_truthy():
    """A container with anything in it is truthy, as is a non-zero number."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_structured_truthy.jaz
        an-array():
            🐆.v = ["a"]
            🐆.retval = "truthy" if 🐆.v else "falsy"

        an-object():
            🐆.v.key = "value"
            🐆.retval = "truthy" if 🐆.v else "falsy"

        a-number():
            🐆.v = 1
            🐆.retval = "truthy" if 🐆.v else "falsy"

        boolean-true():
            🐆.v = true
            🐆.retval = "truthy" if 🐆.v else "falsy"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        for target in ["an-array", "an-object", "a-number", "boolean-true"]:
            assert evaluate(root_module, f"🐭.{target}()") == "truthy"


def test_truthiness_is_decided_on_the_value_not_its_rendering():
    """An empty array is falsy even though it renders as the non-empty text `[]`."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_truthiness_vs_rendering.jaz
        build():
            🐆.v = []
            🐆.rendered = "[🐆.v]"
            🐆.decided = "truthy" if 🐆.v else "falsy"
            🐆.retval = "🐆.rendered is 🐆.decided"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # The rendering is two characters of text; the value is still empty.
        assert evaluate(root_module, "🐭.build()") == "[[]] is falsy"


def test_a_structured_value_survives_a_function_call():
    """A structured value passes as an argument and comes back as a return value."""
    if True:
        # Config
        jazzoo_fn = save_fixture("""# test_structured_across_calls.jaz
        [private]
        _describe(config):
            🐆.retval = "name=🐆.config.name"

        build():
            🐆.config.name = "jane"
            🐆.retval = 🐭._describe(config=🐆.config)
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.build()") == "name=jane"


def test_a_call_path_and_a_field_path_do_not_collide():
    """`🐭.a.b` is lexically a module-alias call and a field lookup at once. A call
    wins - it is the only reading with a trailing `()` - and a same-named variable
    still resolves as a field."""
    if True:
        # Config
        save_fixture("""# collide_lib.jaz
        build():
            #!/usr/bin/env bash
            echo "from the imported function"
        """)

        jazzoo_fn = save_fixture("""# test_call_field_collision.jaz
        from ./collide_lib.jaz import build as docker

        🐭.docker-config.build = "from the variable"

        as-a-call():
            🐆.retval = 🐭.docker.build()

        as-a-field():
            🐆.retval = 🐭.docker-config.build
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.as-a-call()") == "from the imported function"
        assert evaluate(root_module, "🐭.as-a-field()") == "from the variable"


def test_a_module_variable_holds_structure_across_an_import():
    """🐭 scoping is unchanged by structured values: an imported accessor reads and
    writes the object in its own defining module."""
    if True:
        # Config
        save_fixture("""# structured_store.jaz
        🐭.state.count = "0"

        set-count(to):
            🐭.state.count = 🐆.to

        get-count():
            🐆.retval = 🐭.state.count
        """)

        jazzoo_fn = save_fixture("""# test_structured_import.jaz
        🐭.state.count = "caller-owns-this"

        from ./structured_store.jaz import (set-count, get-count) as s

        build():
            🐭.s.set-count(to="42")
            🐆.theirs = 🐭.s.get-count()
            🐆.retval = "theirs=🐆.theirs mine=🐭.state.count"
        """)

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert (
            evaluate(root_module, "🐭.build()")
            == "theirs=42 mine=caller-owns-this"
        )
