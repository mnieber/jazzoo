from config_tests.config_test_env import Context, TestEnv

BASE_YAML = """
    compose:
      use_dockerfile_local: false
    deploy:
      host: shop.example.com
      port: 8443
    """

LOCAL_YAML = """
    compose:
      use_dockerfile_local: true
    """

JAZZOO_SOURCE = """
    ⚙️.load_config(path=⚙️.module.dirname / "config/base.yaml")
    ⚙️.load_config(path=⚙️.module.dirname / "config/local.yaml", required=false)

    build(local=⚙️.get_config(path="/compose/use_dockerfile_local", default=false)):
        echo 🐆.local

    deploy():
        echo "deploying to {{ ⚙️.get_config(path="/deploy/host") }}"

    show-deploy():
        🐆.deploy = ⚙️.get_config(path="/deploy")
        echo "🐆.deploy.host:🐆.deploy.port"
    """


def create_env(context: Context):
    return Env(context)


def test_jazzoo_file_reads_config(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a base config file, and a jazzoo file that loads it, and also loads
    # an optional local config file that does not exist yet. The default of the
    # local parameter of build is read from the config, and deploy reads the host
    # in a substitution.
    #
    # build should print the value of the base config, and deploy the host.
    if env.step(
        env.write_config("config/base.yaml", BASE_YAML),
        env.write_file("jazzoo", JAZZOO_SOURCE),
        env.parse_module("jazzoo"),
        env.evaluate("🐭.build()", store_as="build_output"),
        env.evaluate("🐭.deploy()", store_as="deploy_output"),
    ):
        assert env.build_output == "false"
        assert env.deploy_output == "deploying to shop.example.com"

    # We call build with local=true.
    #
    # The argument should win over the config.
    if env.step(
        env.evaluate("🐭.build(local=true)"),
    ):
        assert env.output == "true"

    # We add the local config file, which switches use_dockerfile_local on, and
    # load the jazzoo file again.
    #
    # build should print the value of the local config: the default is read from
    # the merged config.
    if env.step(
        env.write_config("config/local.yaml", LOCAL_YAML),
        env.parse_module("jazzoo"),
        env.evaluate("🐭.build()"),
    ):
        assert env.output == "true"

    # We read the whole deploy section into a variable, and print its fields.
    #
    # The section should be an object, whose fields can be reached by name.
    if env.step(
        env.evaluate("🐭.show-deploy()"),
    ):
        assert env.output == "shop.example.com:8443"


class Env(TestEnv):
    def __post_init__(self):
        super().__post_init__()
        self.build_output = None
        self.deploy_output = None
