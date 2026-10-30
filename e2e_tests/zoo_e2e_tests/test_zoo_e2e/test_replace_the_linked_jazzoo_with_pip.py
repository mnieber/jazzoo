import os

from zoo_e2e_tests.zoo_e2e_test_env import COPY_DIR, VENV, WHEELS_DIR, Context, TestEnv

SHOW_MARKER = "import jazzoo; print(jazzoo.MARKER)"


def create_env(context: Context):
    return Env(context)


def test_replace_the_linked_jazzoo_with_pip(context: Context):
    # Create the test environment
    env = create_env(context)

    # We have a source tree with a copy of jazzoo, without package metadata, and
    # the project shop. In shop, we run the zoo of the source tree:
    # `zoo env --init --create-venv`.
    #
    # zoo should create a venv with pip, which links the copy.
    if env.step(
        env.create_linked_venv("shop"),
        env.remember_copy(),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.exists(env.path(f"{VENV}/bin/pip"))

    # In the venv, we run `pip list --format=json`.
    #
    # pip should show the link as an editable install of jazzoo 0.0.0 that
    # points to the copy.
    if env.step(
        env.run_pip(VENV, "list", "--format=json"),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.listed_package("jazzoo")["version"] == "0.0.0"
        assert env.listed_package("jazzoo")["editable_project_location"] == (
            env.path(COPY_DIR)
        )

    # We have a wheel of jazzoo 0.2.0, and run
    # `pip install --no-index --find-links wheels jazzoo==0.2.0`.
    #
    # pip should uninstall the link, which removes all its files from the venv,
    # but nothing of the copy, and install the wheel.
    if env.step(
        env.build_jazzoo_wheel("0.2.0"),
        env.run_pip(
            VENV,
            "install",
            "--no-index",
            "--find-links",
            env.path(WHEELS_DIR),
            "jazzoo==0.2.0",
        ),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.link_files(VENV) == []
        assert env.copy_snapshot() == env.remembered_copy

    # We import jazzoo in the venv.
    #
    # The venv should import the jazzoo of the wheel.
    if env.step(
        env.run_python_in_venv(VENV, SHOW_MARKER),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.completed.stdout.splitlines() == ["wheel 0.2.0"]

    # We run `pip list --format=json` again.
    #
    # pip should show jazzoo 0.2.0, which is not an editable install.
    if env.step(
        env.run_pip(VENV, "list", "--format=json"),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert env.listed_package("jazzoo")["version"] == "0.2.0"
        assert "editable_project_location" not in env.listed_package("jazzoo")

    # We run `pip uninstall -y jazzoo`.
    #
    # pip should remove the jazzoo of the wheel, and the copy should still be
    # unchanged.
    if env.step(
        env.run_pip(VENV, "uninstall", "-y", "jazzoo"),
    ):
        assert env.completed.returncode == 0, env.completed.stderr
        assert not env.exists(os.path.join(env.site_packages(VENV), "jazzoo"))
        assert env.copy_snapshot() == env.remembered_copy


class Env(TestEnv):
    pass
