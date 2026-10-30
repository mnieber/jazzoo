import os
import shutil
import sys
import typing as T

from jazzoo.settings import DEFAULT_FILENAMES, get_path_dirs, get_zoo_bin_dir
from jazzoo.zoo.actions.create_venv import create_venv
from jazzoo.zoo.errors import (
    NoRootFileError,
    NotAVenvError,
    NoZooInVenvError,
    VenvExistsError,
    VenvInUseError,
    ZooEnvExistsError,
    ZooLinkExistsError,
)
from jazzoo.zoo.models.zoo_env import ZooEnv
from jazzoo.zoo.rules.find_zoo_env_of_venv import find_zoo_env_of_venv
from jazzoo.zoo.rules.get_zoo_env_dir import get_zoo_env_dir
from jazzoo.zoo.rules.get_zoo_link import get_zoo_link
from jazzoo.zoo.rules.validate_zoo_env_name import validate_zoo_env_name

# Deactivate only when the shell has the function: a shell may inherit VIRTUAL_ENV
# without it, from the shell that started it
ACTIVATE_BASH = """export JAZZOO_ENV={name}
if declare -F deactivate >/dev/null; then
    deactivate
fi
source {env_dir}/venv_dir/bin/activate
"""

ACTIVATE_FISH = """set -gx JAZZOO_ENV {name}
if functions -q deactivate
    deactivate
end
source {env_dir}/venv_dir/bin/activate.fish
"""


def init_zoo_env(
    name: str,
    root_dir: str,
    venv_dir: str,
    create: bool = False,
    with_pip: bool = True,
) -> ZooEnv:
    # Everything is checked before anything is written. With create, venv_dir is
    # the venv to create.
    env_dir = get_zoo_env_dir(name)
    link = get_zoo_link(name)
    zoo_script = os.path.join(venv_dir, "bin", "zoo")
    _check(name, root_dir, venv_dir, create, env_dir, link, zoo_script)

    # Undo what was created when a later step fails, so that --init can be retried
    created: T.List[str] = []
    try:
        if create:
            created.append(venv_dir)
            create_venv(venv_dir, prompt=name, with_pip=with_pip)

        created.append(env_dir)
        _write_env_dir(name, env_dir, root_dir, venv_dir)

        if not os.path.islink(link):
            os.makedirs(os.path.dirname(link), exist_ok=True)
            created.append(link)
            os.symlink(zoo_script, link)
    except BaseException:
        for path in reversed(created):
            _remove(path)
        raise

    bin_dir = get_zoo_bin_dir()
    if bin_dir not in get_path_dirs():
        print(
            f"zoo: {bin_dir} is not on the PATH, so zoo-{name} cannot be found",
            file=sys.stderr,
        )

    return ZooEnv(name=name, root_dir=root_dir, venv_dir=venv_dir)


def _check(name, root_dir, venv_dir, create, env_dir, link, zoo_script):
    validate_zoo_env_name(name)
    if os.path.lexists(env_dir):
        raise ZooEnvExistsError(f"zoo environment {name} already exists")

    if not any(os.path.exists(os.path.join(root_dir, f)) for f in DEFAULT_FILENAMES):
        raise NoRootFileError(
            f"no jazzoo file in {root_dir}; expected one of: "
            + ", ".join(DEFAULT_FILENAMES)
        )

    if create:
        if os.path.lexists(venv_dir):
            raise VenvExistsError(
                f"{venv_dir} already exists; use --use-venv to register it"
            )
    else:
        if not os.path.exists(os.path.join(venv_dir, "pyvenv.cfg")):
            raise NotAVenvError(f"not a venv (it has no pyvenv.cfg): {venv_dir}")
        if not os.path.exists(zoo_script):
            raise NoZooInVenvError(f"jazzoo is not installed in the venv {venv_dir}")
        other = find_zoo_env_of_venv(venv_dir)
        if other is not None:
            raise VenvInUseError(
                f"the venv {venv_dir} belongs to zoo environment {other.name}"
            )

    if os.path.lexists(link) and not (
        os.path.islink(link) and os.readlink(link) == zoo_script
    ):
        raise ZooLinkExistsError(f"{link} already exists")


def _write_env_dir(name, env_dir, root_dir, venv_dir):
    os.makedirs(env_dir)
    os.symlink(root_dir, os.path.join(env_dir, "root_dir"))
    os.symlink(venv_dir, os.path.join(env_dir, "venv_dir"))
    for shell, template in (("bash", ACTIVATE_BASH), ("fish", ACTIVATE_FISH)):
        with open(os.path.join(env_dir, f"activate.{shell}"), "w") as f:
            f.write(template.format(name=name, env_dir=env_dir))


def _remove(path: str):
    if os.path.islink(path) or os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)
