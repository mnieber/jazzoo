from config_tests.config_test_env import Context, TestEnv

from jazzoo.config import ConfigFileError


def create_env(context: Context):
    return Env(context)


def test_config_files(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a config file with a syntax error on line 2.
    #
    # Reading from it should raise a ConfigFileError that names the file and the
    # line.
    if env.step(
        env.write_config("broken.yaml", "root:\n  src: /src: oops\n"),
        env.use_config_files("broken.yaml"),
        env.get_and_catch_error("/root/src"),
    ):
        assert isinstance(env.error, ConfigFileError)
        assert f"{env.path('broken.yaml')}:2" in str(env.error)

    # We have a config file whose top level is a list.
    #
    # It should raise a ConfigFileError that names the file.
    if env.step(
        env.write_config("list.yaml", "- web\n- api\n"),
        env.use_config_files("list.yaml"),
        env.get_and_catch_error("/"),
    ):
        assert isinstance(env.error, ConfigFileError)
        assert env.path("list.yaml") in str(env.error)

    # We have a config file with two YAML documents.
    #
    # It should raise a ConfigFileError.
    if env.step(
        env.write_config("two_docs.yaml", "root: 1\n---\nother: 2\n"),
        env.use_config_files("two_docs.yaml"),
        env.get_and_catch_error("/"),
    ):
        assert isinstance(env.error, ConfigFileError)

    # We have a config file with a Python object tag.
    #
    # It should raise a ConfigFileError, and not construct the object.
    if env.step(
        env.write_config(
            "python_tag.yaml", "run: !!python/object/apply:os.getcwd []\n"
        ),
        env.use_config_files("python_tag.yaml"),
        env.get_and_catch_error("/"),
    ):
        assert isinstance(env.error, ConfigFileError)

    # JAZZOO_CONFIG_FILES lists a file that does not exist.
    #
    # It should raise a ConfigFileError that names the file.
    if env.step(
        env.use_config_files("missing.yaml"),
        env.get_and_catch_error("/"),
    ):
        assert isinstance(env.error, ConfigFileError)
        assert env.path("missing.yaml") in str(env.error)


class Env(TestEnv):
    pass
