from config_tests.config_test_env import Context, TestEnv

LAYER_DIR_YAML = """
    jazzoo:
      includes: ["${SHOP_LAYER_DIR:-layers}/docker.yaml"]
    """


def create_env(context: Context):
    return Env(context)


# get_config caches the config per list of files, and copies the environment when it
# builds the cache, so every step writes its files in a directory of its own.
def test_include_expansion(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a base file that includes a layer in a dir that an environment
    # variable names.
    #
    # The include should use the variable.
    if env.step(
        env.set_env("SHOP_CONFIG_DIR", env.path("var/layers")),
        env.write_config(
            "var/base.yaml",
            """
            jazzoo:
              includes: ["${SHOP_CONFIG_DIR}/docker.yaml"]
            """,
        ),
        env.write_config("var/layers/docker.yaml", "docker:\n  shell: sh\n"),
        env.use_config_files("var/base.yaml"),
        env.get("/jazzoo/includes"),
    ):
        assert env.value == [env.path("var/layers/docker.yaml")]

    # We have a base file whose include uses a variable with a default, and the
    # variable is unset.
    #
    # The include should use the default, which is relative to the base file.
    if env.step(
        env.unset_env("SHOP_LAYER_DIR"),
        env.write_config("unset/base.yaml", LAYER_DIR_YAML),
        env.write_config("unset/layers/docker.yaml", "docker: {}\n"),
        env.use_config_files("unset/base.yaml"),
        env.get("/jazzoo/includes"),
    ):
        assert env.value == [env.path("unset/layers/docker.yaml")]

    # The variable is empty.
    #
    # The include should use the default.
    if env.step(
        env.set_env("SHOP_LAYER_DIR", ""),
        env.write_config("empty/base.yaml", LAYER_DIR_YAML),
        env.write_config("empty/layers/docker.yaml", "docker: {}\n"),
        env.use_config_files("empty/base.yaml"),
        env.get("/jazzoo/includes"),
    ):
        assert env.value == [env.path("empty/layers/docker.yaml")]

    # The variable holds a relative path.
    #
    # The include should use the variable, resolved against the base file.
    if env.step(
        env.set_env("SHOP_LAYER_DIR", "custom"),
        env.write_config("set/base.yaml", LAYER_DIR_YAML),
        env.write_config("set/custom/docker.yaml", "docker: {}\n"),
        env.use_config_files("set/base.yaml"),
        env.get("/jazzoo/includes"),
    ):
        assert env.value == [env.path("set/custom/docker.yaml")]

    # We have a base file that includes a layer below the home directory.
    #
    # The leading ~ should be the home directory, taken from HOME.
    if env.step(
        env.set_env("HOME", env.path("home")),
        env.write_config(
            "tilde/base.yaml", "jazzoo:\n  includes: [~/layers/docker.yaml]\n"
        ),
        env.write_config("home/layers/docker.yaml", "docker: {}\n"),
        env.use_config_files("tilde/base.yaml"),
        env.get("/jazzoo/includes"),
    ):
        assert env.value == [env.path("home/layers/docker.yaml")]

    # We have a base file that includes odd~.yaml.
    #
    # A ~ that is not at the start should be part of the name.
    if env.step(
        env.write_config("odd/base.yaml", "jazzoo:\n  includes: [odd~.yaml]\n"),
        env.write_config("odd/odd~.yaml", "odd: 1\n"),
        env.use_config_files("odd/base.yaml"),
        env.get("/jazzoo/includes"),
    ):
        assert env.value == [env.path("odd/odd~.yaml")]

    # We have a base file that includes $SHOP_NAME.yaml and $${x}.yaml.
    #
    # $NAME without braces should stay literal text, and $${ should yield ${.
    if env.step(
        env.set_env("SHOP_NAME", "shop"),
        env.write_config(
            "literal/base.yaml",
            """
            jazzoo:
              includes: [$SHOP_NAME.yaml, "$${x}.yaml"]
            """,
        ),
        env.write_config("literal/$SHOP_NAME.yaml", "a: 1\n"),
        env.write_config("literal/${x}.yaml", "b: 1\n"),
        env.use_config_files("literal/base.yaml"),
        env.get("/jazzoo/includes"),
    ):
        assert env.value == [
            env.path("literal/$SHOP_NAME.yaml"),
            env.path("literal/${x}.yaml"),
        ]

    # We call prepare_config for a base file whose include uses a variable, and
    # then change the variable before we read the config.
    #
    # The include should use the variable as it was when prepare_config copied
    # the environment.
    if env.step(
        env.set_env("SHOP_LAYER_DIR", "first"),
        env.write_config("copy/base.yaml", LAYER_DIR_YAML),
        env.write_config("copy/first/docker.yaml", "docker: {}\n"),
        env.write_config("copy/second/docker.yaml", "docker: {}\n"),
        env.use_config_files("copy/base.yaml"),
        env.prepare_config(),
        env.set_env("SHOP_LAYER_DIR", "second"),
        env.get("/jazzoo/includes"),
    ):
        assert env.value == [env.path("copy/first/docker.yaml")]

    # We do the same for a base file whose include uses the home directory.
    #
    # The include should use HOME as it was when prepare_config copied the
    # environment.
    if env.step(
        env.set_env("HOME", env.path("first_home")),
        env.write_config(
            "copy_home/base.yaml", "jazzoo:\n  includes: [~/docker.yaml]\n"
        ),
        env.write_config("first_home/docker.yaml", "docker: {}\n"),
        env.write_config("second_home/docker.yaml", "docker: {}\n"),
        env.use_config_files("copy_home/base.yaml"),
        env.prepare_config(),
        env.set_env("HOME", env.path("second_home")),
        env.get("/jazzoo/includes"),
    ):
        assert env.value == [env.path("first_home/docker.yaml")]


class Env(TestEnv):
    pass
