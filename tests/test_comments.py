"""Comments in a .jaz file (design section 6).

A full-line `#` is discarded at parse time, which is what makes it inert in every
place a line could otherwise have an effect: substitution, the console, and
⚙️.stdout.
"""

import pytest

from jazzoo import evaluate, parse_module
from jazzoo.errors import ResolutionError
from jazzoo.runtime.utils.test_utils import save_fixture


def test_a_full_line_comment_is_discarded():
    """A line whose first non-whitespace character is `#` is a jazzoo comment. It is
    discarded when the file is parsed, so it never reaches an interpreter."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_discarded.jaz
        build():
            # fetch the sources first
            echo "done"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.build()") == "done"


def test_a_comment_is_not_echoed_to_the_console(capsys):
    """A comment is not echoed to the console."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_not_echoed.jaz
        build():
            # fetch the sources first
            @echo "done"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)
        evaluate(root_module, "🐭.build()")
        captured = capsys.readouterr()

        # Assert
        # `@` hides the one real command, so the comment is the only thing that
        # could have reached the console.
        assert "fetch the sources" not in captured.out
        assert "#" not in captured.out
        assert captured.out.strip() == "done"


def test_a_comment_is_not_substituted():
    """A comment is not substituted, so a reference inside one is just text and an
    unresolvable one is not an error."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_not_substituted.jaz
        build():
            # this mentions 🐆.never-defined, which does not resolve
            echo "done"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        # The same reference outside a comment would raise ResolutionError.
        assert evaluate(root_module, "🐭.build()") == "done"

    """The reference really is unresolvable - it is the comment that spares it."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_reference_really_fails.jaz
        build():
            echo "this mentions 🐆.never-defined"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        with pytest.raises(ResolutionError):
            evaluate(root_module, "🐭.build()")


def test_a_comment_leaves_stdout_alone():
    """A comment is not a block, so it leaves ⚙️.stdout alone - adding one between a
    command and the line that reads its output does not change what that line sees."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_stdout_untouched.jaz
        build():
            @echo "first"
            # a comment between the command and the line that reads it
            🐆.captured = ⚙️.stdout
            @echo "[🐆.captured]"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.build()") == "[first\n]"

    """A comment as the final line likewise does not become the return value."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_trailing_comment_retval.jaz
        build():
            echo "the real output"
            # nothing after this point produces output
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.build()") == "the real output"


def test_a_shebang_is_not_a_comment():
    """The exception is `#!`, which stays a shebang - including bare `#!` returning
    to jazzoo mode."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_shebang_survives.jaz
        build():
            #!/usr/bin/env python3
            print("from python")

            #!
            echo "back in jazzoo mode: ⚙️.output"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.build()") == "back in jazzoo mode: from python"


def test_comments_inside_a_shebang_block_are_passed_through():
    """Comments are stripped only from jazzoo-mode lines. Inside a shebang block the
    body belongs to that interpreter, so a `#` line is passed through untouched."""
    if True:
        # Config
        # The Python comment must survive: if it were stripped, the `if` body would
        # be empty and the block would be a SyntaxError.
        jazzoo_fn = save_fixture(
            """# test_block_comments_survive.jaz
        build():
            #!/usr/bin/env python3
            if True:
                # this comment is the only thing keeping the block parseable
                print("still valid")
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.build()") == "still valid"


def test_only_whole_lines_are_comments():
    """Only whole lines are comments. A `#` after other text on a line is part of
    that line, because it is ordinary syntax in the shells jazzoo drives."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_trailing_hash.jaz
        build():
            echo "a # b"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.build()") == "a # b"


def test_a_comment_may_be_indented_to_any_depth():
    """It is the first non-whitespace character that decides, so a comment may sit
    at any indentation - including inside a local function body."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_indented_comment.jaz
        build():
            # at body level
            🐆.dump():
                    # indented further, inside the local function
                    echo "from the local function"

            🐆.retval = 🐆.dump()
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.build()") == "from the local function"


def test_a_comment_ending_in_a_backslash_does_not_continue():
    """A trailing `\\` continues a jazzoo-mode line, but not a comment: as in bash,
    the line after the comment is an ordinary line."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_comment_backslash.jaz
        build():
            # files live under C:\\
            echo "done"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.build()") == "done"
