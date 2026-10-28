from config_tests.config_test_env import Context, TestEnv

from jazzoo.config import ConfigExpansionError

CONFIG_YAML = """
    build:
      threads: 2
      flags: [-O2, -g]
      paths:
        src: /src
        out: /out
      name: shop
      debug: true
      release: false
      tag: null
    refs:
      threads: ${/build/threads}
      flags: ${/build/flags}
      paths: ${/build/paths}
      label: ${/build/name}-${/build/threads}-${/build/debug}-${/build/release}-[${/build/tag}]
      flags_text: flags=${/build/flags}
      paths_text: paths=${/build/paths}
    chain:
      a: ${/chain/b}
      b: ${/chain/c}
      c: done
    nested:
      inner:
        out: ${/build/paths/out}/${/build/name}
    missing: ${/build/version}
    cycle:
      a: ${/cycle/b}
      b: ${/cycle/a}
    broken: ${SHOP_UNSET_VARIABLE}
    """


def create_env(context: Context):
    return Env(context)


def test_references(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a config file with references, some of which are broken.
    if env.step(
        env.unset_env("SHOP_UNSET_VARIABLE"),
        env.write_config("config.yaml", CONFIG_YAML),
        env.use_config_files("config.yaml"),
    ):
        pass

    # We read values that consist of a single reference.
    #
    # Each should keep the type of the referenced value.
    if env.step(
        env.get("/refs/threads", store_as="threads"),
        env.get("/refs/flags", store_as="flags"),
        env.get("/refs/paths", store_as="paths"),
    ):
        assert env.threads == 2
        assert env.flags == ["-O2", "-g"]
        assert env.paths == {"src": "/src", "out": "/out"}

    # We read a value with references inside a longer string.
    #
    # The references should be rendered: a string as is, a number as JSON, a
    # boolean as true or false, and null as the empty string.
    if env.step(
        env.get("/refs/label"),
    ):
        assert env.value == "shop-2-true-false-[]"

    # We read a value with a reference to a list inside a longer string.
    #
    # It should raise a ConfigExpansionError.
    if env.step(
        env.get_and_catch_error("/refs/flags_text"),
    ):
        assert isinstance(env.error, ConfigExpansionError)

    # We read a value with a reference to a dict inside a longer string.
    #
    # It should raise a ConfigExpansionError.
    if env.step(
        env.get_and_catch_error("/refs/paths_text"),
    ):
        assert isinstance(env.error, ConfigExpansionError)

    # We read a value that references a value that references another value.
    #
    # The references should chain.
    if env.step(
        env.get("/chain/a"),
    ):
        assert env.value == "done"

    # We read a dict whose values contain references.
    #
    # The values inside the dict should be expanded, recursively.
    if env.step(
        env.get("/nested"),
    ):
        assert env.value == {"inner": {"out": "/out/shop"}}

    # We read a value that references a path that does not exist.
    #
    # It should raise a ConfigExpansionError that names the missing path, the path
    # of the value, and the config file.
    if env.step(
        env.get_and_catch_error("/missing"),
    ):
        assert isinstance(env.error, ConfigExpansionError)
        assert "/build/version" in str(env.error)
        assert "/missing" in str(env.error)
        assert env.path("config.yaml") in str(env.error)

    # We read a value that is part of a reference cycle.
    #
    # It should raise a ConfigExpansionError that lists the paths in the cycle.
    if env.step(
        env.get_and_catch_error("/cycle/a"),
    ):
        assert isinstance(env.error, ConfigExpansionError)
        assert "/cycle/a" in str(env.error)
        assert "/cycle/b" in str(env.error)

    # We read a value while other values in the config are broken.
    #
    # Expansion is lazy, so the broken values should not matter.
    if env.step(
        env.get("/build/name"),
    ):
        assert env.value == "shop"

    # We read a broken value with a default.
    #
    # The value exists, so the default should not apply: it should raise a
    # ConfigExpansionError.
    if env.step(
        env.get_and_catch_error("/broken", default="fallback"),
    ):
        assert isinstance(env.error, ConfigExpansionError)


class Env(TestEnv):
    def __post_init__(self):
        super().__post_init__()
        self.threads = None
        self.flags = None
        self.paths = None
