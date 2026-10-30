from config_tests.config_test_env import Context, TestEnv

from jazzoo.config import ConfigExpansionError, ConfigFileError


def create_env(context: Context):
    return Env(context)


# get_config caches the config per list of files, so every step writes its files in
# a directory of its own.
def test_include_errors(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a base file that includes a file that does not exist.
    #
    # It should raise a ConfigFileError that names the base file and the absolute
    # path of the missing file.
    if env.step(
        env.write_config("missing/base.yaml", "jazzoo:\n  includes: [docker.yaml]\n"),
        env.use_config_files("missing/base.yaml"),
        env.get_and_catch_error("/"),
    ):
        assert isinstance(env.error, ConfigFileError)
        assert env.path("missing/base.yaml") in str(env.error)
        assert env.path("missing/docker.yaml") in str(env.error)

    # We call prepare_config for the same files.
    #
    # It should raise the same ConfigFileError.
    if env.step(
        env.prepare_config_and_catch_error(),
    ):
        assert isinstance(env.error, ConfigFileError)
        assert env.path("missing/docker.yaml") in str(env.error)

    # We have a base file that includes a layer, which includes a file that does
    # not exist.
    #
    # The error should name the layer, which contains the include.
    if env.step(
        env.write_config("nested/base.yaml", "jazzoo:\n  includes: [docker.yaml]\n"),
        env.write_config("nested/docker.yaml", "jazzoo:\n  includes: [common.yaml]\n"),
        env.use_config_files("nested/base.yaml"),
        env.get_and_catch_error("/"),
    ):
        assert isinstance(env.error, ConfigFileError)
        assert env.path("nested/docker.yaml") in str(env.error)
        assert env.path("nested/common.yaml") in str(env.error)

    # We have base files whose includes are a string, a list with a number, and a
    # dict.
    #
    # Each should raise a ConfigFileError that names the base file.
    for name, includes in [
        ("string.yaml", "docker.yaml"),
        ("number.yaml", "[1]"),
        ("dict.yaml", "{a: b}"),
    ]:
        if env.step(
            env.write_config(f"malformed/{name}", f"jazzoo:\n  includes: {includes}\n"),
            env.use_config_files(f"malformed/{name}"),
            env.get_and_catch_error("/"),
        ):
            assert isinstance(env.error, ConfigFileError)
            assert env.path(f"malformed/{name}") in str(env.error)

    # We have a config file whose jazzoo key is a number.
    #
    # The jazzoo key is reserved, so it should raise a ConfigFileError that names
    # the file.
    if env.step(
        env.write_config("reserved/base.yaml", "jazzoo: 3\n"),
        env.use_config_files("reserved/base.yaml"),
        env.get_and_catch_error("/"),
    ):
        assert isinstance(env.error, ConfigFileError)
        assert env.path("reserved/base.yaml") in str(env.error)

    # We have a base file that includes a layer with a syntax error on line 2.
    #
    # It should raise a ConfigFileError that names the layer and the line.
    if env.step(
        env.write_config("broken/base.yaml", "jazzoo:\n  includes: [docker.yaml]\n"),
        env.write_config("broken/docker.yaml", "docker:\n  shell: sh: oops\n"),
        env.use_config_files("broken/base.yaml"),
        env.get_and_catch_error("/"),
    ):
        assert isinstance(env.error, ConfigFileError)
        assert f"{env.path('broken/docker.yaml')}:2" in str(env.error)

    # We have a base file with an include that references a config value.
    #
    # The config is not built yet, so it should raise a ConfigFileError that names
    # the base file and the include.
    if env.step(
        env.write_config(
            "reference/base.yaml",
            """
            jazzoo:
              includes: ["${/root/dir}/docker.yaml"]
            root:
              dir: layers
            """,
        ),
        env.write_config("reference/layers/docker.yaml", "docker: {}\n"),
        env.use_config_files("reference/base.yaml"),
        env.get_and_catch_error("/"),
    ):
        assert isinstance(env.error, ConfigFileError)
        assert env.path("reference/base.yaml") in str(env.error)
        assert "${/root/dir}/docker.yaml" in str(env.error)

    # We have a base file with an include that uses an environment variable that is
    # not set.
    #
    # It should raise a ConfigFileError that names the base file and the variable.
    if env.step(
        env.unset_env("SHOP_CONFIG_DIR"),
        env.write_config(
            "unset/base.yaml",
            """
            jazzoo:
              includes: ["${SHOP_CONFIG_DIR}/docker.yaml"]
            """,
        ),
        env.use_config_files("unset/base.yaml"),
        env.get_and_catch_error("/"),
    ):
        assert isinstance(env.error, ConfigFileError)
        assert env.path("unset/base.yaml") in str(env.error)
        assert "SHOP_CONFIG_DIR" in str(env.error)

    # We have a base file that includes a layer with a value that uses an
    # environment variable that is not set. We read that value.
    #
    # It should raise a ConfigExpansionError that names the layer, which supplied
    # the value, and not the base file.
    if env.step(
        env.unset_env("SHOP_DB_HOST"),
        env.write_config("value/base.yaml", "jazzoo:\n  includes: [db.yaml]\n"),
        env.write_config("value/db.yaml", "db:\n  host: ${SHOP_DB_HOST}\n"),
        env.use_config_files("value/base.yaml"),
        env.get_and_catch_error("/db/host"),
    ):
        assert isinstance(env.error, ConfigExpansionError)
        assert env.path("value/db.yaml") in str(env.error)
        assert env.path("value/base.yaml") not in str(env.error)


class Env(TestEnv):
    pass
