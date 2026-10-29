import pytest
from interactive_tests.interactive_test_env import Context


@pytest.fixture
def context(tmp_path, monkeypatch, capfd):
    # An interactive block writes to file descriptors 1 and 2 directly, which capsys
    # does not see. capfd has the same interface, and captures at the
    # file-descriptor level.
    return Context(tmp_path=tmp_path, monkeypatch=monkeypatch, capsys=capfd)
