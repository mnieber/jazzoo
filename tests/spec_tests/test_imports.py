import os
from jazzoo.modules.rules.parse_module import parse_module
from jazzoo.modules.rules.get_child_module_by_name import get_child_module_by_name
from jazzoo.modules.rules.eval import eval
from jazzoo.utils.test_utils import get_fixture_fn

def test_single_import():
    # Config
    jazzoo_fn = get_fixture_fn("test_single_import.jazzoo")

    # Run
    root_module = parse_module(jazzoo_fn)
    foo_module = get_child_module_by_name(root_module, "foo")

    # Assert
    assert root_module.filename == os.path.join(os.path.dirname(jazzoo_fn), "foo.jaz")
    assert eval(root_module, "🐐.test") == "123"
    assert eval(foo_module, "🐭.test") == "mouse"

