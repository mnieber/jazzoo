import typing as T

from config_tests.config_test_env import Context, TestEnv

BASE_YAML = """
    env: dev
    root:
      project_dir: ${PROJECT_DIR}
      src: ${/root/project_dir}/src
    urls:
      dev: http://localhost:8000
      prod: https://shop.example.com
    api_url: ${/urls/${/env}}
    """

LOCAL_YAML = """
    env: prod
    root:
      project_dir: /srv/shop
    """


def create_env(context: Context):
    return Env(context)


def test_script_reads_expanded_values(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a base config that takes the project dir from the environment, builds
    # the source dir from it, and picks the api url that matches the env.
    #
    # The source dir should be expanded from PROJECT_DIR, and the api url should be
    # the dev url.
    if env.step(
        env.set_env("PROJECT_DIR", "/home/jane/projects/shop"),
        env.write_config("base.yaml", BASE_YAML),
        env.use_config_files("base.yaml"),
        env.get("/root/src", store_as="src"),
        env.get("/api_url", store_as="api_url"),
    ):
        assert env.src == "/home/jane/projects/shop/src"
        assert env.api_url == "http://localhost:8000"

    # We add a local config that sets the project dir and switches the env to prod.
    #
    # The references in the base config should see the merged values: the source
    # dir is below the new project dir, and the api url is the prod url.
    if env.step(
        env.write_config("local.yaml", LOCAL_YAML),
        env.use_config_files("base.yaml", "local.yaml"),
        env.get("/root/src", store_as="src"),
        env.get("/api_url", store_as="api_url"),
    ):
        assert env.src == "/srv/shop/src"
        assert env.api_url == "https://shop.example.com"


class Env(TestEnv):
    def __post_init__(self):
        super().__post_init__()
        self.src: T.Any = None
        self.api_url: T.Any = None
