from zoo_e2e_tests.zoo_e2e_test_env import COPY_DIR, VENV, WHEELS_DIR, Context, TestEnv

SHOW_JAZZOO_FILE = "import jazzoo; print(jazzoo.__file__)"

SHOW_MARKER = "import jazzoo; print(jazzoo.MARKER)"


def create_env(context: Context):
    return Env(context)


def test_pip_install_the_same_version(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a venv with pip that links a copy of jazzoo, which has the version
    # 0.0.0, and a wheel of jazzoo 0.0.0.
    if env.step(
        env.create_linked_venv("shop"),
        env.remember_copy(),
        env.build_jazzoo_wheel("0.0.0"),
    ):
        assert env.completed.returncode == 0, env.completed.stderr

    # We run `pip install --no-index --find-links wheels jazzoo==0.0.0`.
    #
    # pip sees that version installed, so it should say so, and keep the link.
    if env.step(
        env.run_pip(
            VENV,
            "install",
            "--no-index",
            "--find-links",
            env.path(WHEELS_DIR),
            "jazzoo==0.0.0",
        ),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert "Requirement already satisfied" in env.completed.stdout
        assert env.link_files(VENV) != []

    # We import jazzoo in the venv.
    #
    # The venv should still import the copy.
    if env.step(
        env.run_python_in_venv(VENV, SHOW_JAZZOO_FILE),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout.splitlines() == [
            env.path(f"{COPY_DIR}/__init__.py")
        ]

    # We run the same command with --force-reinstall.
    #
    # pip should replace the link with the wheel, and leave the copy unchanged.
    if env.step(
        env.run_pip(
            VENV,
            "install",
            "--force-reinstall",
            "--no-index",
            "--find-links",
            env.path(WHEELS_DIR),
            "jazzoo==0.0.0",
        ),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.link_files(VENV) == []
        assert env.copy_snapshot() == env.remembered_copy

    # We import jazzoo in the venv again.
    #
    # The venv should import the jazzoo of the wheel.
    if env.step(
        env.run_python_in_venv(VENV, SHOW_MARKER),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout.splitlines() == ["wheel 0.0.0"]


class Env(TestEnv):
    pass
