from zoo_e2e_tests.zoo_e2e_test_env import VENV, Context, TestEnv

IMPORT_JAZZOO = "import jazzoo"


def create_env(context: Context):
    return Env(context)


def test_pip_uninstall_the_link(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a venv with pip that links a copy of jazzoo.
    if env.step(
        env.create_linked_venv("shop"),
        env.remember_copy(),
    ):
        assert env.completed.returncode == 0, env.completed.stderr

    # We import jazzoo in the venv.
    #
    # Python should have run _jazzoo_link at startup, and compiled it to
    # __pycache__.
    if env.step(
        env.run_python_in_venv(VENV, IMPORT_JAZZOO),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert [path for path in env.link_files(VENV) if "__pycache__" in path]

    # We run `pip uninstall -y jazzoo`.
    #
    # pip should remove every file of the link (also the compiled _jazzoo_link
    # and the console scripts), and nothing of the copy.
    if env.step(
        env.run_pip(VENV, "uninstall", "-y", "jazzoo"),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.link_files(VENV) == []
        assert env.copy_snapshot() == env.remembered_copy

    # We import jazzoo in the venv again.
    #
    # jazzoo is no longer installed, so this should fail.
    if env.step(
        env.run_python_in_venv(VENV, IMPORT_JAZZOO),
    ):
        assert env.completed.returncode != 0
        assert "ModuleNotFoundError: No module named 'jazzoo'" in env.completed.stderr


class Env(TestEnv):
    pass
