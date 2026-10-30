from completions_tests.completions_test_env import Context, TestEnv


def create_env(context: Context):
    return Env(context)


def test_complete_values(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have the project shop, with a directory src, and a dotfile .env.
    if env.step(
        env.write_jazzoo(),
        env.write_file("shop/src/main.py", ""),
        env.write_file("shop/src/app/__init__.py", ""),
        env.write_file("shop/.env", "MODE=debug\n"),
    ):
        pass

    # We complete the value `mode=src/`.
    #
    # It should offer the entries of src, with the name of the parameter in
    # front.
    if env.step(
        env.complete_jaz("build", "mode=src/"),
    ):
        assert sorted(env.candidates()) == ["mode=src/app/", "mode=src/main.py"]

    # We complete the value `mode=`.
    #
    # The dotfile .env should not be offered.
    if env.step(
        env.complete_jaz("build", "mode="),
    ):
        assert "mode=.env" not in env.candidates()
        assert "mode=src/" in env.candidates()

    # We complete the value `mode=.`.
    #
    # The typed part starts with a dot, so .env should be offered.
    if env.step(
        env.complete_jaz("build", "mode=."),
    ):
        assert env.candidates() == ["mode=.env"]

    # We change to the directory work, which has its own files, and complete a
    # value with `--file ../shop/jazzoo`.
    #
    # The paths should be relative to the current directory, not to the directory
    # of the jazzoo file.
    if env.step(
        env.write_file("work/notes.txt", ""),
        env.change_dir("work"),
        env.complete_jaz("--file", "../shop/jazzoo", "build", "mode="),
    ):
        assert env.candidates() == ["mode=notes.txt"]

    # We complete the word after `--file`.
    #
    # It should offer the file names of the current directory, without a name in
    # front.
    if env.step(
        env.complete_jaz("--file", ""),
    ):
        assert env.candidates() == ["notes.txt"]

    # We complete a value in a directory that does not exist.
    #
    # It should offer nothing, and print no error.
    if env.step(
        env.change_dir("shop"),
        env.complete_jaz("build", "mode=nope/"),
    ):
        assert env.exit_code == 0
        assert env.output == ""
        assert env.printed_err == ""


class Env(TestEnv):
    pass
