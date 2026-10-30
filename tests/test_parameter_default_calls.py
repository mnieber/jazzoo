from jazzoo import evaluate, parse_module
from jazzoo.runtime.utils.test_utils import save_fixture


def test_a_parameter_default_may_call_a_function():
    """A default is an expression, so it may be a call, with arguments of its own.
    A parenthesis inside a string default is part of the string."""
    if True:
        # Config
        jazzoo_fn = save_fixture(
            """# test_param_default_call.jaz
        mode(suffix="-x"):
            echo "release🐆.suffix"

        build(mode=🐭.mode(suffix="-y"), label="(none)"):
            echo "🐆.mode 🐆.label"
        """
        )

        # Run
        root_module = parse_module(jazzoo_fn)

        # Assert
        assert evaluate(root_module, "🐭.build()") == "release-y (none)"
        assert evaluate(root_module, '🐭.build(mode="dev")') == "dev (none)"
