import pytest

from jazzoo import (
    JazzooError,
    ParseError,
    ResolutionError,
    evaluate,
    parse_module,
)
from jazzoo.runtime.utils.test_utils import save_fixture


def test_bare_references_are_substituted():
    """Jazzoo variables can be referenced directly in shell lines and strings,
    without any escaping."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_bare_refs.jaz
        🐐.log-level = "high"

        debug(name="me"):
            echo "log level: 🐐.log-level for user: 🐆.name"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.debug()") == "log level: high for user: me"


def test_hyphens_are_part_of_variable_names():
    """The `-` character is valid in variable names, so a shell option name and the
    variable name can be identical."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_hyphen_names.jaz
        🐐.log-level = "high"

        debug():
            echo "--log-level=🐐.log-level"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # The `--log-level=` prefix is literal text; only 🐐.log-level is substituted.
        assert evaluate(root_module, "🐭.debug()") == "--log-level=high"


def test_braced_references_when_adjacent_to_text():
    """`{{ }}` delimits a reference that is adjacent to other text."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_braced.jaz
        🐐.log-level = "high"

        debug():
            echo "log level: {{ 🐐.log-level }}-setting"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.debug()") == "log level: high-setting"


def test_braces_may_hold_an_expression():
    """`{{ }}` holds any expression, not only a reference: a ternary, a boolean or a
    pipe is evaluated and its value substituted. The quotes of a string literal
    belong to jazzoo, so they are gone before the shell sees the line."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_braced_expressions.jaz
        run(cmd="", file="/tmp/build/app.tar.gz"):
            echo "{{ 🐆.cmd if 🐆.cmd else "bash" }}|{{ 🐆.cmd or "sh" }}|{{ 🐆.file | ⚙️.basename }}"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.run()") == "bash|sh|app.tar.gz"
        assert evaluate(root_module, '🐭.run(cmd="fish")') == "fish|fish|app.tar.gz"


def test_a_malformed_braced_expression_is_a_parse_error():
    """A braced expression is parsed when the file is loaded, so a malformed one is
    a ParseError up front - it never renders as an empty string."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_braced_malformed.jaz
        run(cmd=""):
            echo "{{ 🐆.cmd if 🐆.cmd }}"
        """
        )

        # Run and assert
        with pytest.raises(ParseError):
            parse_module(jazzoo_fn)


def test_braces_without_sigils_are_left_alone():
    """Braces that contain no sigil are ignored by jazzoo and pass through."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_plain_braces.jaz
        debug():
            echo "a {{ plain }} brace and a { single } one"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert (
            evaluate(root_module, "🐭.debug()")
            == "a {{ plain }} brace and a { single } one"
        )


def test_escaped_sigil_suppresses_substitution():
    """Prefixing the sigil with `\\` suppresses substitution, printing the literal
    emoji and name instead."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_escaped_sigil.jaz
        🐭.tracing = "on"

        debug():
            echo "with \\🐭.tracing set to: 🐭.tracing"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # The escaped reference is literal; the unescaped one is substituted.
        assert evaluate(root_module, "🐭.debug()") == "with 🐭.tracing set to: on"


def test_backslash_terminates_a_variable_name():
    """A `\\` after a reference ends the variable name, so the text that follows is
    literal even though it would otherwise extend the name."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_name_terminator.jaz
        🐭.tracing = "on"

        debug():
            echo "🐭.tracing\\.com"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # Without the backslash the dot would continue the name into a structured
        # lookup, so the escape is what makes ".com" literal text.
        assert evaluate(root_module, "🐭.debug()") == "on.com"

    """The escape is required, not optional: an unescaped dot is a path segment."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_unescaped_dot_is_a_path.jaz
        🐭.tracing = "on"

        debug():
            echo "🐭.tracing.com"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # `tracing` holds a string, so it has no `com` field.
        with pytest.raises(ResolutionError):
            evaluate(root_module, "🐭.debug()")


def test_a_dot_that_cannot_start_a_segment_is_literal_text():
    """A dot only continues the name when what follows could begin a segment, so a
    reference can end a sentence without an escape."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_sentence_dot.jaz
        greet(name="jane", dir="/tmp"):
            🐆.retval = "Hello 🐆.name."

        mid-sentence(name="jane"):
            🐆.retval = "Hello 🐆.name. Welcome"

        before-a-slash(dir="/tmp"):
            🐆.retval = "🐆.dir./config"

        before-a-hyphen(name="jane"):
            🐆.retval = "🐆.name.-suffix"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.greet()") == "Hello jane."
        assert evaluate(root_module, "🐭.mid-sentence()") == "Hello jane. Welcome"
        assert evaluate(root_module, "🐭.before-a-slash()") == "/tmp./config"
        # A hyphen cannot start a segment, the same reason a name may not end on one.
        assert evaluate(root_module, "🐭.before-a-hyphen()") == "jane.-suffix"


def test_a_dot_before_a_name_character_is_still_a_lookup():
    """The escape is only needed where the dot really is indistinguishable from a
    field lookup - a dot followed immediately by a name character."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_dot_before_name_char.jaz
        🐭.host = "example"

        needs-the-escape():
            🐆.retval = "🐭.host.com"

        digit-is-a-segment():
            🐆.hosts = ["a", "b"]
            🐆.retval = 🐆.hosts.1

        underscore-is-a-segment():
            🐆.cfg._private = "hidden"
            🐆.retval = 🐆.cfg._private
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # `host` holds a string, so it has no `com` field.
        with pytest.raises(ResolutionError):
            evaluate(root_module, "🐭.needs-the-escape()")
        assert evaluate(root_module, "🐭.digit-is-a-segment()") == "b"
        assert evaluate(root_module, "🐭.underscore-is-a-segment()") == "hidden"


def test_the_name_terminator_works_in_expression_position():
    """A `\\` ends the name in an expression too, not only in a shell line - which is
    what makes the migration from the old dotted-suffix behaviour possible."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_terminator_in_expression.jaz
        🐭.host = "example"
        🐭.full = 🐭.host\\.com

        debug():
            🐆.local = 🐭.host\\.org
            🐆.retval = "🐭.full/🐆.local"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.full") == "example.com"
        assert evaluate(root_module, "🐭.debug()") == "example.com/example.org"


def test_escaping_inside_braces_yields_a_literal_braced_reference():
    """`{{ \\🐐.x }}` produces the literal text `{{ 🐐.x }}`."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_literal_braced.jaz
        🐐.log-level = "high"

        debug():
            echo "Jazzoo supports the {{ \\🐐.log-level }}-setting syntax"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert (
            evaluate(root_module, "🐭.debug()")
            == "Jazzoo supports the {{ 🐐.log-level }}-setting syntax"
        )


def test_all_three_namespaces_substitute():
    """🐐, 🐭 and 🐆 references all substitute, each against its own scope."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_all_sigils.jaz
        🐐.global-value = "g"
        🐭.module-value = "m"

        debug(local-value="l"):
            echo "🐐.global-value 🐭.module-value 🐆.local-value"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.debug()") == "g m l"


def test_system_variables_substitute():
    """⚙️ system variables substitute like any other reference."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_system_vars.jaz
        debug():
            echo "running ⚙️.module.basename"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.debug()") == "running test_system_vars.jaz"


def test_substitution_happens_inside_shebang_blocks():
    """Substitution applies to shebang block lines too, not just jazzoo-mode lines."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_subst_in_shebang.jaz
        🐭.greeting = "hello"

        debug():
            #!/usr/bin/env python3
            print("🐭.greeting from python")
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.debug()") == "hello from python"


def test_braced_reference_names_a_python_variable():
    """A braced reference is not a leading sigil, so it passes through the sweep as
    a regular line - which is how a Python variable gets a name from a jazzoo value."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_braced_python_name.jaz
        🐭.variable = "foo"

        debug():
            #!/usr/bin/env python3
            {{ 🐭.variable }} = "bar"
            print(foo)
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.debug()") == "bar"


def test_values_are_substituted_without_escaping():
    """Substitution is textual: jazzoo does not quote or escape what it splices, so
    a value containing interpreter syntax becomes interpreter syntax."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_no_escaping.jaz
        🐭.fragment = "--dry-run --verbose"

        debug():
            echo 🐭.fragment
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # The value splits into two shell words - this is what makes fragments like
        # 🐆.dry-run work, and is also why untrusted values need ⚙️.sh-quote.
        assert evaluate(root_module, "🐭.debug()") == "--dry-run --verbose"


def test_sh_quote_renders_a_value_as_one_shell_word():
    """⚙️.sh-quote renders a value as a single, safely quoted POSIX shell word, so it
    cannot expand, split, or terminate the surrounding command."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_sh_quote.jaz
        🐭.spaced = "two words"
        🐭.hostile = "; echo pwned"

        count-words():
            🐆.safe = 🐭.spaced | ⚙️.sh-quote
            #!/usr/bin/env bash
            printf '%s' 🐆.safe | wc -w | tr -d ' '

        stays-literal():
            🐆.safe = 🐭.hostile | ⚙️.sh-quote
            echo 🐆.safe
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # Quoted, the value is one word rather than two.
        assert evaluate(root_module, "🐭.count-words()") == "2"
        # The metacharacters are inert - no second command runs.
        assert evaluate(root_module, "🐭.stays-literal()") == "; echo pwned"


def test_env_variables_are_substituted(monkeypatch):
    """⚙️.env.NAME refers to an environment variable, and substitutes like any
    other reference. All-caps is a convention, not a requirement."""
    if True:
        # Config
        monkeypatch.setenv("JAZZOO_LOG_LEVEL", "high")
        monkeypatch.setenv("jazzoo_lower", "yes")

        jazzoo_fn = save_fixture(
            """# test_env_basic.jaz
        debug():
            echo "⚙️.env.JAZZOO_LOG_LEVEL and ⚙️.env.jazzoo_lower"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.debug()") == "high and yes"


def test_an_unset_reference_is_a_resolution_error(monkeypatch):
    """By default every reference must resolve: an unset variable raises a
    ResolutionError rather than substituting an empty string."""
    if True:
        # Config
        monkeypatch.delenv("JAZZOO_ABSENT", raising=False)

        jazzoo_fn = save_fixture(
            """# test_unset_errors.jaz
        from-env():
            echo "⚙️.env.JAZZOO_ABSENT"

        from-global():
            echo "🐐.never-assigned"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        with pytest.raises(ResolutionError):
            evaluate(root_module, "🐭.from-env()")
        with pytest.raises(ResolutionError):
            evaluate(root_module, "🐭.from-global()")


def test_question_mark_marks_a_reference_as_possibly_absent(monkeypatch):
    """`?` resolves an absent reference to the empty string instead of raising."""
    if True:
        # Config
        monkeypatch.delenv("JAZZOO_CI", raising=False)

        jazzoo_fn = save_fixture(
            """# test_optional_ref.jaz
        debug():
            echo "[⚙️.env.JAZZOO_CI?]"

        as-a-flag():
            🐆.ci-flag = "--ci" if ⚙️.env.JAZZOO_CI? else ""
            echo "[🐆.ci-flag]"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.debug()") == "[]"
        # An empty string is falsy, so the flag is not added.
        assert evaluate(root_module, "🐭.as-a-flag()") == "[]"

        # And when it is set, it resolves normally.
        monkeypatch.setenv("JAZZOO_CI", "1")
        assert evaluate(root_module, "🐭.debug()") == "[1]"
        assert evaluate(root_module, "🐭.as-a-flag()") == "[--ci]"


def test_default_applies_when_the_value_is_empty(monkeypatch):
    """`:-` supplies a default used when the value is empty. The reference must
    still exist."""
    if True:
        # Config
        monkeypatch.setenv("JAZZOO_EMPTY", "")
        monkeypatch.setenv("JAZZOO_SET", "debug")
        monkeypatch.delenv("JAZZOO_ABSENT", raising=False)

        jazzoo_fn = save_fixture(
            """# test_default_on_empty.jaz
        when-empty():
            echo "⚙️.env.JAZZOO_EMPTY:-info"

        when-set():
            echo "⚙️.env.JAZZOO_SET:-info"

        when-absent():
            echo "⚙️.env.JAZZOO_ABSENT:-info"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.when-empty()") == "info"
        assert evaluate(root_module, "🐭.when-set()") == "debug"
        # Without `?`, absence is still an error - `:-` only covers emptiness.
        with pytest.raises(ResolutionError):
            evaluate(root_module, "🐭.when-absent()")


def test_optional_with_default_covers_absent_and_empty(monkeypatch):
    """`?:-` combines both: the default applies when the reference is absent or
    empty."""
    if True:
        # Config
        monkeypatch.delenv("JAZZOO_ABSENT", raising=False)
        monkeypatch.setenv("JAZZOO_EMPTY", "")
        monkeypatch.setenv("JAZZOO_SET", "debug")

        jazzoo_fn = save_fixture(
            """# test_optional_default.jaz
        when-absent():
            echo "⚙️.env.JAZZOO_ABSENT?:-info"

        when-empty():
            echo "⚙️.env.JAZZOO_EMPTY?:-info"

        when-set():
            echo "⚙️.env.JAZZOO_SET?:-info"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.when-absent()") == "info"
        assert evaluate(root_module, "🐭.when-empty()") == "info"
        assert evaluate(root_module, "🐭.when-set()") == "debug"


def test_markers_apply_to_every_namespace():
    """`?` and `:-` apply uniformly to 🐐, 🐭, 🐆 and ⚙️.env."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_markers_uniform.jaz
        🐭.assigned = ""

        globals():
            echo "🐐.never-set?:-from-goat"

        modules():
            echo "🐭.assigned:-from-mouse"

        locals():
            echo "🐆.never-set?:-from-leopard"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.globals()") == "from-goat"
        # 🐭.assigned exists but is empty, so `:-` alone is enough.
        assert evaluate(root_module, "🐭.modules()") == "from-mouse"
        assert evaluate(root_module, "🐭.locals()") == "from-leopard"


def test_defaults_may_be_bare_or_quoted(monkeypatch):
    """A default may be a bare string or a quoted one; bare defaults end at the
    first whitespace."""
    if True:
        # Config
        monkeypatch.delenv("JAZZOO_GREETING", raising=False)

        jazzoo_fn = save_fixture(
            """# test_default_quoting.jaz
        bare():
            echo "[⚙️.env.JAZZOO_GREETING?:-hello]"

        quoted():
            echo "[⚙️.env.JAZZOO_GREETING?:-"hello there"]"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.bare()") == "[hello]"
        assert evaluate(root_module, "🐭.quoted()") == "[hello there]"


def test_markers_work_in_braced_references(monkeypatch):
    """Both markers are part of the reference syntax, so they work in braced
    positions as well as bare ones."""
    if True:
        # Config
        monkeypatch.delenv("JAZZOO_LOG_LEVEL", raising=False)

        jazzoo_fn = save_fixture(
            """# test_markers_braced.jaz
        debug():
            echo "{{ ⚙️.env.JAZZOO_LOG_LEVEL?:-info }}-setting"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.debug()") == "info-setting"


def test_backslash_terminates_the_name_before_a_marker(monkeypatch):
    """`\\` still terminates the variable name, so a `?:-` after it is literal text
    rather than a marker."""
    if True:
        # Config
        monkeypatch.setenv("JAZZOO_HOST", "example.com")

        jazzoo_fn = save_fixture(
            """# test_marker_escaped.jaz
        debug():
            echo "⚙️.env.JAZZOO_HOST\\?:-literal"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.debug()") == "example.com?:-literal"


def test_a_colon_after_a_reference_is_not_a_default(monkeypatch):
    """`:-` was chosen over a bare `:` so that the colons that follow references
    routinely in shell lines keep their literal meaning."""
    if True:
        # Config
        monkeypatch.setenv("JAZZOO_HOST", "example.com")
        monkeypatch.setenv("JAZZOO_HOME", "/home/me")

        jazzoo_fn = save_fixture(
            """# test_literal_colon.jaz
        port():
            echo "⚙️.env.JAZZOO_HOST:8080"

        volume():
            echo "-v ⚙️.env.JAZZOO_HOME:/data"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.port()") == "example.com:8080"
        assert evaluate(root_module, "🐭.volume()") == "-v /home/me:/data"


def test_system_variables_are_read_only():
    """All ⚙️ variables are read-only - a .jaz file can never assign to ⚙️."""
    if True:
        # Config
        at_top_level = save_fixture(
            """# test_readonly_top_level.jaz
        ⚙️.module.basename = "mine.jaz"
        """
        )

        in_a_body = save_fixture(
            """# test_readonly_in_body.jaz
        debug():
            ⚙️.stdout = "mine"
        """
        )

        # Run / Assert
        # Assigning to ⚙️ is rejected wherever it appears. The specific subclass is
        # whatever the grammar decides - rejecting the sigil on an assignment LHS
        # makes it a ParseError - so this pins only the JazzooError base.
        with pytest.raises(JazzooError):
            parse_module(at_top_level)
        with pytest.raises(JazzooError):
            parse_module(in_a_body)
