from config_tests.config_test_env import Context, TestEnv

from jazzoo.config import ConfigKeyError


def create_env(context: Context):
    return Env(context)


# get_config caches the config per list of files, so every step writes its files in
# a directory of its own.
def test_includes(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a base file that includes a and b, where a includes c. Each file sets
    # the keys from its own position onwards, so a later file overrides the keys of
    # an earlier one.
    #
    # The order should be c, a, b, the base file: the base file wins, and a
    # layer's own includes come before the layer.
    if env.step(
        env.write_config(
            "order/base.yaml",
            """
            jazzoo:
              includes: [a.yaml, b.yaml]
            k4: base
            """,
        ),
        env.write_config(
            "order/a.yaml",
            """
            jazzoo:
              includes: [c.yaml]
            k2: a
            k3: a
            k4: a
            """,
        ),
        env.write_config("order/b.yaml", "k3: b\nk4: b\n"),
        env.write_config("order/c.yaml", "k1: c\nk2: c\nk3: c\nk4: c\n"),
        env.use_config_files("order/base.yaml"),
        env.get("/", store_as="config"),
        env.get("/jazzoo/includes"),
    ):
        assert {key: env.config[key] for key in ["k1", "k2", "k3", "k4"]} == {
            "k1": "c",
            "k2": "a",
            "k3": "b",
            "k4": "base",
        }
        assert env.value == [
            env.path("order/c.yaml"),
            env.path("order/a.yaml"),
            env.path("order/b.yaml"),
        ]

    # We have a cycle: a includes b, which includes a. Only a is in
    # JAZZOO_CONFIG_FILES.
    #
    # The config should load, with b before a, so a wins. The includes list should
    # hold b once.
    if env.step(
        env.write_config(
            "cycle/a.yaml",
            """
            jazzoo:
              includes: [b.yaml]
            name: a
            """,
        ),
        env.write_config(
            "cycle/b.yaml",
            """
            jazzoo:
              includes: [a.yaml]
            name: b
            """,
        ),
        env.use_config_files("cycle/a.yaml"),
        env.get("/name", store_as="name"),
        env.get("/jazzoo/includes"),
    ):
        assert env.name == "a"
        assert env.value == [env.path("cycle/b.yaml")]

    # We have a file that includes itself.
    #
    # The config should load, and the includes list should be empty, because the
    # file itself is in JAZZOO_CONFIG_FILES.
    if env.step(
        env.write_config(
            "self/self.yaml",
            """
            jazzoo:
              includes: [self.yaml]
            name: self
            """,
        ),
        env.use_config_files("self/self.yaml"),
        env.get("/name", store_as="name"),
        env.get("/jazzoo/includes"),
    ):
        assert env.name == "self"
        assert env.value == []

    # We have a diamond: the base file includes left and right, which both include
    # common. Left overrides a value of common.
    #
    # Common should be merged once, at its first position (before left), so the
    # value of left still holds.
    if env.step(
        env.write_config(
            "diamond/base.yaml",
            """
            jazzoo:
              includes: [left.yaml, right.yaml]
            """,
        ),
        env.write_config(
            "diamond/left.yaml",
            """
            jazzoo:
              includes: [common.yaml]
            color: left
            """,
        ),
        env.write_config(
            "diamond/right.yaml",
            """
            jazzoo:
              includes: [common.yaml]
            """,
        ),
        env.write_config("diamond/common.yaml", "color: common\n"),
        env.use_config_files("diamond/base.yaml"),
        env.get("/color", store_as="color"),
        env.get("/jazzoo/includes"),
    ):
        assert env.color == "left"
        assert env.value == [
            env.path("diamond/common.yaml"),
            env.path("diamond/left.yaml"),
            env.path("diamond/right.yaml"),
        ]

    # We have a base file and a local file in JAZZOO_CONFIG_FILES, which both
    # include the docker layer. The base file overrides the shell of the layer.
    #
    # The layer should be merged once, before the base file, so the shell of the
    # base file still holds. The includes list should hold the layer once.
    if env.step(
        env.write_config(
            "shared/base.yaml",
            """
            jazzoo:
              includes: [docker.yaml]
            docker:
              shell: bash
            """,
        ),
        env.write_config(
            "shared/local.yaml",
            """
            jazzoo:
              includes: [docker.yaml]
            """,
        ),
        env.write_config("shared/docker.yaml", "docker:\n  shell: sh\n"),
        env.use_config_files("shared/base.yaml", "shared/local.yaml"),
        env.get("/docker/shell", store_as="shell"),
        env.get("/jazzoo/includes"),
    ):
        assert env.shell == "bash"
        assert env.value == [env.path("shared/docker.yaml")]

    # JAZZOO_CONFIG_FILES holds the base file and the docker layer, which the base
    # file already includes.
    #
    # The layer should be merged once, before the base file, so the base file
    # wins. The layer should be in the includes list.
    if env.step(
        env.write_config(
            "top/base.yaml",
            """
            jazzoo:
              includes: [docker.yaml]
            docker:
              shell: bash
            """,
        ),
        env.write_config("top/docker.yaml", "docker:\n  shell: sh\n"),
        env.use_config_files("top/base.yaml", "top/docker.yaml"),
        env.get("/docker/shell", store_as="shell"),
        env.get("/jazzoo/includes"),
    ):
        assert env.shell == "bash"
        assert env.value == [env.path("top/docker.yaml")]

    # We have a base file in a config dir that includes layers/docker.yaml, which
    # includes common.yaml, and a file outside the config dir by its absolute path.
    #
    # An include should resolve against the dir of the file that contains it, so
    # common.yaml is the one in the layers dir. The absolute include should work.
    if env.step(
        env.write_config(
            "paths/config/base.yaml",
            f"""
            jazzoo:
              includes:
                - layers/docker.yaml
                - {env.path("paths/elsewhere/extra.yaml")}
            """,
        ),
        env.write_config(
            "paths/config/layers/docker.yaml",
            """
            jazzoo:
              includes: [common.yaml]
            """,
        ),
        env.write_config("paths/config/layers/common.yaml", "common: layers\n"),
        env.write_config("paths/config/common.yaml", "common: config\n"),
        env.write_config("paths/elsewhere/extra.yaml", "extra: 1\n"),
        env.use_config_files("paths/config/base.yaml"),
        env.get("/common", store_as="common"),
        env.get("/extra", store_as="extra"),
        env.get("/jazzoo/includes"),
    ):
        assert env.common == "layers"
        assert env.extra == 1
        assert env.value == [
            env.path("paths/config/layers/common.yaml"),
            env.path("paths/config/layers/docker.yaml"),
            env.path("paths/elsewhere/extra.yaml"),
        ]

    # We have a base file that includes ./docker.yaml and docker.yaml.
    #
    # They are the same file, so the includes list should hold it once, as a
    # normalized absolute path.
    if env.step(
        env.write_config(
            "same/base.yaml",
            """
            jazzoo:
              includes: [./docker.yaml, docker.yaml]
            """,
        ),
        env.write_config("same/docker.yaml", "docker:\n  shell: sh\n"),
        env.use_config_files("same/base.yaml"),
        env.get("/jazzoo/includes"),
    ):
        assert env.value == [env.path("same/docker.yaml")]

    # We have a config file without includes.
    #
    # The config should have no jazzoo key.
    if env.step(
        env.write_config("none/base.yaml", "name: base\n"),
        env.use_config_files("none/base.yaml"),
        env.get("/", store_as="config"),
        env.get_and_catch_error("/jazzoo"),
    ):
        assert env.config == {"name": "base"}
        assert isinstance(env.error, ConfigKeyError)

    # We have a config file with an empty includes list.
    #
    # The includes list should be empty.
    if env.step(
        env.write_config("empty/base.yaml", "jazzoo:\n  includes: []\n"),
        env.use_config_files("empty/base.yaml"),
        env.get("/jazzoo/includes"),
    ):
        assert env.value == []

    # We have a config file whose jazzoo key is null, and one whose includes key is
    # null.
    #
    # Both mean no includes, so the config should load.
    if env.step(
        env.write_config("null/jazzoo.yaml", "jazzoo: null\nname: a\n"),
        env.write_config("null/includes.yaml", "jazzoo:\n  includes: null\nname: b\n"),
        env.use_config_files("null/jazzoo.yaml"),
        env.get("/name", store_as="name"),
        env.use_config_files("null/includes.yaml"),
        env.get("/name"),
    ):
        assert env.name == "a"
        assert env.value == "b"

    # We have a base file with a key of its own under jazzoo, next to its includes,
    # and a layer that sets another key under jazzoo.
    #
    # Both keys should be merged like any other config.
    if env.step(
        env.write_config(
            "other/base.yaml",
            """
            jazzoo:
              includes: [layer.yaml]
              note: base
            """,
        ),
        env.write_config("other/layer.yaml", "jazzoo:\n  color: blue\n"),
        env.use_config_files("other/base.yaml"),
        env.get("/jazzoo/note", store_as="note"),
        env.get("/jazzoo/color", store_as="color"),
    ):
        assert env.note == "base"
        assert env.color == "blue"

    # We have a base file that includes odd$${x}.yaml, which is the file odd${x}.yaml.
    #
    # The includes list should hold the path as it is, without expanding the ${x}
    # in it, also when we read the whole config.
    if env.step(
        env.write_config(
            "dollar/base.yaml",
            """
            jazzoo:
              includes: ["odd$${x}.yaml"]
            """,
        ),
        env.write_config("dollar/odd${x}.yaml", "odd: 1\n"),
        env.use_config_files("dollar/base.yaml"),
        env.get("/jazzoo/includes"),
        env.get("/", store_as="config"),
    ):
        assert env.value == [env.path("dollar/odd${x}.yaml")]
        assert env.config["jazzoo"]["includes"] == [env.path("dollar/odd${x}.yaml")]
        assert env.config["odd"] == 1


class Env(TestEnv):
    def __post_init__(self):
        super().__post_init__()
        self.config = None
        self.name = None
        self.color = None
        self.shell = None
        self.common = None
        self.extra = None
        self.note = None
