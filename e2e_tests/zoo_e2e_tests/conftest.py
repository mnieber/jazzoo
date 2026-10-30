import pytest
from zoo_e2e_tests.zoo_e2e_test_env import Context


@pytest.fixture
def context(tmp_path, monkeypatch, capfd):
    # As in zoo_tests: capfd also captures what subprocesses write to fds 1 and 2
    return Context(tmp_path=tmp_path, monkeypatch=monkeypatch, capsys=capfd)
