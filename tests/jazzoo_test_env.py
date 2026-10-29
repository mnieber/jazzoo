import os
import textwrap
import typing as T
from pathlib import Path

import pytest

from jazzoo import evaluate, parse_module
from jazzoo.utils.dataclass import dataclass


@dataclass
class Context:
    tmp_path: Path
    monkeypatch: pytest.MonkeyPatch
    capsys: pytest.CaptureFixture


class TestEnv:
    __test__ = False

    def __init__(self, context: Context):
        self.context = context
        self.root_module: T.Any = None
        self.output: T.Optional[str] = None
        self.error: T.Optional[Exception] = None

        # ⚙️.load_config changes os.environ directly. Registering the variable with
        # monkeypatch makes sure that it starts unset and is restored afterwards.
        context.monkeypatch.delenv("JAZZOO_CONFIG_FILES", raising=False)

        self.__post_init__()

    def __post_init__(self):
        pass

    def step(self, *_):
        return True

    def write_file(self, name: str, text: str):
        """Writes a file below tmp_path. The text is dedented, so that a test can
        indent it like the surrounding code."""
        path = Path(self.path(name))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")

    def change_dir(self, name: str = ""):
        self.context.monkeypatch.chdir(self.path(name))

    def set_env(self, name: str, value: str):
        self.context.monkeypatch.setenv(name, value)

    def unset_env(self, name: str):
        self.context.monkeypatch.delenv(name, raising=False)

    def parse_module(self, name: str):
        self.root_module = parse_module(self.path(name))

    def parse_module_and_catch_error(self, name: str):
        self.error = None
        try:
            self.parse_module(name)
        except Exception as error:
            self.error = error

    def evaluate(self, expression: str, store_as: str = "output"):
        setattr(self, store_as, evaluate(self.root_module, expression))

    def evaluate_and_catch_error(self, expression: str):
        self.error = None
        try:
            self.evaluate(expression)
        except Exception as error:
            self.error = error

    # Queries

    def path(self, name: str) -> str:
        return str(self.context.tmp_path / name)

    def env_var(self, name: str) -> T.Optional[str]:
        return os.environ.get(name)
