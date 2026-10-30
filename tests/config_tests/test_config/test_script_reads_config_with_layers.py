from config_tests.config_test_env import Context, TestEnv

BASE_YAML = """
    jazzoo:
      includes:
        - tmux.yaml
        - docker.yaml

    root:
      project_dir: /home/jane/shop

    docker:
      shell: bash
    """

TMUX_YAML = """
    tmux:
      session: shop
    """

DOCKER_YAML = """
    jazzoo:
      includes:
        - common.yaml

    docker:
      compose_project: shop
      shell: sh
      timeout: 30
    """

COMMON_YAML = """
    docker:
      timeout: 10
      registry: registry.example.com
    """

LOCAL_YAML = """
    jazzoo:
      includes:
        - local_docker.yaml

    root:
      project_dir: /home/jane/work/shop
    """

LOCAL_DOCKER_YAML = """
    docker:
      compose_project: shop_dev
    """


def create_env(context: Context):
    return Env(context)


def test_script_reads_config_with_layers(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a base config file that includes a tmux layer and a docker layer. The
    # docker layer includes a common layer. Only the base file is in
    # JAZZOO_CONFIG_FILES. A script reads a value of each file.
    #
    # It should find the values of the base file and of all its layers.
    if env.step(
        env.write_config("base.yaml", BASE_YAML),
        env.write_config("tmux.yaml", TMUX_YAML),
        env.write_config("docker.yaml", DOCKER_YAML),
        env.write_config("common.yaml", COMMON_YAML),
        env.use_config_files("base.yaml"),
        env.get("/root/project_dir", store_as="project_dir"),
        env.get("/tmux/session", store_as="session"),
        env.get("/docker/compose_project", store_as="compose_project"),
        env.get("/docker/registry", store_as="registry"),
    ):
        assert env.project_dir == "/home/jane/shop"
        assert env.session == "shop"
        assert env.compose_project == "shop"
        assert env.registry == "registry.example.com"

    # The script reads the docker section, which the base file and two of its
    # layers set.
    #
    # The base file should win over its layers, and the docker layer over the
    # common layer that it includes. The dicts should be merged.
    if env.step(
        env.get("/docker"),
    ):
        assert env.value == {
            "compose_project": "shop",
            "shell": "bash",
            "timeout": 30,
            "registry": "registry.example.com",
        }

    # The script reads the includes list.
    #
    # It should hold the absolute paths of all the layers, a layer's own includes
    # before the layer.
    if env.step(
        env.get("/jazzoo/includes"),
    ):
        assert env.value == [
            env.path("tmux.yaml"),
            env.path("common.yaml"),
            env.path("docker.yaml"),
        ]

    # We add a local config file after the base file. It includes a layer of its
    # own.
    #
    # The local file and its layer should win over the base file and its layers.
    # The includes list should hold the layers of both files, those of the base
    # file first.
    if env.step(
        env.write_config("local.yaml", LOCAL_YAML),
        env.write_config("local_docker.yaml", LOCAL_DOCKER_YAML),
        env.use_config_files("base.yaml", "local.yaml"),
        env.get("/root/project_dir", store_as="project_dir"),
        env.get("/docker/compose_project", store_as="compose_project"),
        env.get("/jazzoo/includes"),
    ):
        assert env.project_dir == "/home/jane/work/shop"
        assert env.compose_project == "shop_dev"
        assert env.value == [
            env.path("tmux.yaml"),
            env.path("common.yaml"),
            env.path("docker.yaml"),
            env.path("local_docker.yaml"),
        ]


class Env(TestEnv):
    def __post_init__(self):
        super().__post_init__()
        self.project_dir = None
        self.session = None
        self.compose_project = None
        self.registry = None
