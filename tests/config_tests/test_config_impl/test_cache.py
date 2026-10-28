from config_tests.config_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_cache(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a config file with a source dir and a user that comes from the
    # environment, and read the source dir from it.
    if env.step(
        env.set_env("SHOP_USER", "jane"),
        env.write_config("base.yaml", "root:\n  src: /old/src\n  user: ${SHOP_USER}\n"),
        env.use_config_files("base.yaml"),
        env.get("/root/src"),
    ):
        assert env.value == "/old/src"

    # We change the config file on disk, and read the source dir again.
    #
    # The list of config files did not change, so get_config should return the
    # cached value.
    if env.step(
        env.write_config("base.yaml", "root:\n  src: /new/src\n  user: ${SHOP_USER}\n"),
        env.get("/root/src"),
    ):
        assert env.value == "/old/src"

    # We change the user in the environment, and read the user for the first time.
    #
    # get_config should use the copy of the environment that it took when it built
    # the cache, so the user should still be the old one.
    if env.step(
        env.set_env("SHOP_USER", "john"),
        env.get("/root/user"),
    ):
        assert env.value == "jane"

    # We add a second config file to JAZZOO_CONFIG_FILES, and read again.
    #
    # The list changed, so get_config should rebuild the config, and see the new
    # file, the changed contents of the first one, and the changed user.
    if env.step(
        env.write_config("extra.yaml", "root:\n  build: /new/build\n"),
        env.use_config_files("base.yaml", "extra.yaml"),
        env.get("/root"),
    ):
        assert env.value == {"src": "/new/src", "user": "john", "build": "/new/build"}


class Env(TestEnv):
    pass
