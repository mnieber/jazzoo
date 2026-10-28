import os
import typing as T

from jazzoo_test_env import Context, TestEnv as JazzooTestEnv

from jazzoo.config import get_config, prepare_config

__all__ = ["Context", "TestEnv"]


class TestEnv(JazzooTestEnv):
    def __post_init__(self):
        self.value: T.Any = None

    def write_config(self, name: str, yaml_text: str):
        self.write_file(name, yaml_text)

    def use_config_files(self, *names: str):
        """Points JAZZOO_CONFIG_FILES at the given files, like ⚙️.load_config does.

        get_config caches the config per value of JAZZOO_CONFIG_FILES, so a test
        that changes a file after reading it must also use a new list of files.
        """
        self.set_env(
            "JAZZOO_CONFIG_FILES", os.pathsep.join(self.path(name) for name in names)
        )

    def prepare_config(self):
        self.value = prepare_config()

    def prepare_config_and_catch_error(self):
        self.error = None
        try:
            prepare_config()
        except Exception as error:
            self.error = error

    def get(self, path: str, store_as: str = "value", **kwargs: T.Any):
        setattr(self, store_as, get_config(path, **kwargs))

    def get_and_catch_error(self, path: str, **kwargs: T.Any):
        self.error = None
        try:
            get_config(path, **kwargs)
        except Exception as error:
            self.error = error

    # Queries

    def config_files(self) -> T.List[str]:
        value = os.environ.get("JAZZOO_CONFIG_FILES", "")
        return value.split(os.pathsep) if value else []
