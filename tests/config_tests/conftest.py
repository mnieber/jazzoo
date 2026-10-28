import pytest
from config_tests.config_test_env import Context


@pytest.fixture
def context(tmp_path, monkeypatch, capsys):
    return Context(tmp_path=tmp_path, monkeypatch=monkeypatch, capsys=capsys)
