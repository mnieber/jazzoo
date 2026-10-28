import typing as T

from config_tests.config_test_env import Context, TestEnv

BASE_YAML = """
    root:
      src: /home/jane/projects/shop/src
      tags:
        - web
        - api
      database:
        host: localhost
        port: 5432
    """

LOCAL_YAML = """
    root:
      src: /home/jane/work/shop/src
      database:
        port: 6543
    """


def create_env(context: Context):
    return Env(context)


def test_script_reads_merged_config(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a base config file, and point JAZZOO_CONFIG_FILES at it. A script
    # reads the source dir.
    #
    # It should get the source dir of the base config.
    if env.step(
        env.write_config("base.yaml", BASE_YAML),
        env.use_config_files("base.yaml"),
        env.get("/root/src"),
    ):
        assert env.value == "/home/jane/projects/shop/src"

    # We add a local config file that overrides the source dir and the database
    # port, and add it to JAZZOO_CONFIG_FILES. The script reads several values.
    #
    # The source dir should come from the local config. The tags come from the base
    # config, and the database settings are merged.
    if env.step(
        env.write_config("local.yaml", LOCAL_YAML),
        env.use_config_files("base.yaml", "local.yaml"),
        env.get("/root/src", store_as="src"),
        env.get("/root/tags/0", store_as="first_tag"),
        env.get("/root/database", store_as="database"),
        env.get("/", store_as="config"),
    ):
        assert env.src == "/home/jane/work/shop/src"
        assert env.first_tag == "web"
        assert env.database == {"host": "localhost", "port": 6543}
        assert env.config == {
            "root": {
                "src": "/home/jane/work/shop/src",
                "tags": ["web", "api"],
                "database": {"host": "localhost", "port": 6543},
            }
        }


class Env(TestEnv):
    def __post_init__(self):
        super().__post_init__()
        self.src: T.Any = None
        self.first_tag: T.Any = None
        self.database: T.Any = None
        self.config: T.Any = None
