from aliases_tests.aliases_test_env import Context, TestEnv

from jazzoo.aliases.errors import AliasError


def create_env(context: Context):
    return Env(context)


def test_alias_config_errors(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a project, and a config file with a line outside a section.
    if env.step(
        env.write_jazzoo(),
        env.write_aliases("b = build\n"),
    ):
        pass

    # We run jaz b.
    #
    # The file is not valid INI, so this should be an AliasError that names the
    # config file.
    if env.step(
        env.run_jaz_and_catch_error("b"),
    ):
        assert isinstance(env.error, AliasError)
        assert env.error.filename == env.alias_config_file()

    # We run jaz build with the same config file.
    #
    # The target exists, so the config file is not read, and build should run as
    # usual.
    if env.step(
        env.run_jaz("build"),
    ):
        assert env.exit_code == 0
        assert env.output_lines() == ["build mode=release"]

    # We define the alias b twice, and run jaz b.
    #
    # The file is malformed, so this should be an AliasError.
    if env.step(
        env.write_aliases("[alias]\nb = build\nb = greet jane\n"),
        env.run_jaz_and_catch_error("b"),
    ):
        assert isinstance(env.error, AliasError)
        assert env.error.filename == env.alias_config_file()

    # We define an alias whose name is not a valid target path, next to a valid
    # alias, and run both.
    #
    # The invalid name makes the whole file an error, also when the valid alias is
    # looked up, and the error should name the invalid alias.
    if env.step(
        env.write_aliases("[alias]\nb! = build\nfb = fe.build\n"),
        env.run_jaz_and_catch_error("b!"),
    ):
        assert isinstance(env.error, AliasError)
        assert env.error.filename == env.alias_config_file()
        assert '"b!"' in env.error.message

    if env.step(
        env.run_jaz_and_catch_error("fb"),
    ):
        assert isinstance(env.error, AliasError)
        assert '"b!"' in env.error.message

    # We define an alias with an empty expansion, and run it.
    #
    # This should be an AliasError that names the alias.
    if env.step(
        env.write_aliases("[alias]\nb =\n"),
        env.run_jaz_and_catch_error("b"),
    ):
        assert isinstance(env.error, AliasError)
        assert env.error.filename == env.alias_config_file()
        assert '"b"' in env.error.message

    # We run the same alias as the console script does.
    #
    # jaz should print the error, and exit with 1.
    if env.step(
        env.run_jaz_cli("b"),
    ):
        assert env.exit_code == 1
        assert "error: " in env.printed_err
        assert '"b"' in env.printed_err

    # We define an alias with unbalanced quotes, and run it.
    #
    # This should be an AliasError that names the alias.
    if env.step(
        env.write_aliases('[alias]\nb = build "mode=debug\n'),
        env.run_jaz_and_catch_error("b"),
    ):
        assert isinstance(env.error, AliasError)
        assert env.error.filename == env.alias_config_file()
        assert '"b"' in env.error.message


class Env(TestEnv):
    pass
