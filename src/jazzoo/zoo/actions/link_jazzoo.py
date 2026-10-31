import base64
import csv
import hashlib
import json
import os
import shutil
import subprocess
import typing as T
from pathlib import Path

import jazzoo
from jazzoo.settings import MIN_PYTHON_VERSION
from jazzoo.zoo.errors import JazzooLinkError
from jazzoo.zoo.rules.get_jazzoo_version import get_jazzoo_version

# The console scripts of jazzoo, and the entrypoints that they run
CONSOLE_SCRIPTS = {
    "zoo": "jazzoo.runtime.entrypoints.zoo",
    "jaz": "jazzoo.runtime.entrypoints.jazzoo",
    "jazzoo": "jazzoo.runtime.entrypoints.jazzoo",
    "jaz-run": "jazzoo.commands.entrypoints.jaz_run",
}

SCRIPT = """#!{python}
import sys

from {module} import main

if __name__ == "__main__":
    sys.exit(main())
"""

LINK_PTH = "import _jazzoo_link\n"

LINK_MODULE = """import importlib.util
import os
import sys

LINKED_DIR = {linked_dir!r}


class JazzooLinkFinder:
    # Only finds the package jazzoo; its subpackages are found through the package
    @classmethod
    def find_spec(cls, name, path=None, target=None):
        init_file = os.path.join(LINKED_DIR, "__init__.py")
        if name != "jazzoo" or not os.path.isfile(init_file):
            return None
        return importlib.util.spec_from_file_location(
            name, init_file, submodule_search_locations=[LINKED_DIR]
        )


# After the finder of sys.path, so that a real install of jazzoo wins
sys.meta_path.append(JazzooLinkFinder)
"""

METADATA = """Metadata-Version: 2.1
Name: jazzoo
Version: {version}
"""

INSTALLER = "zoo\n"

# Prints the site-packages and the version of a python. It runs in old pythons too.
INSPECT_PYTHON = (
    "import json, sys, sysconfig; print(json.dumps({"
    "'purelib': sysconfig.get_paths()['purelib'], "
    "'version': list(sys.version_info[:2])}))"
)


def link_jazzoo(venv_dir: str) -> T.List[str]:
    # Jazzoo has no dependencies, so linking its package is enough. The venv then
    # follows the jazzoo that linked it, e.g. a development checkout. The link is
    # a linked install that pip can uninstall without touching the linked directory.
    python = os.path.join(venv_dir, "bin", "python")
    site_packages, python_version = _inspect_python(python)
    if python_version < MIN_PYTHON_VERSION:
        raise JazzooLinkError(
            f"cannot link jazzoo into the venv {venv_dir}: its python is "
            f"{_format_version(python_version)}, and jazzoo needs "
            f"{_format_version(MIN_PYTHON_VERSION)} or newer"
        )
    linked_dir = os.path.dirname(jazzoo.__file__)
    version = get_jazzoo_version(linked_dir)
    dist_info = os.path.join(site_packages, f"jazzoo-{version}.dist-info")

    files = {
        os.path.join(site_packages, "_jazzoo_link.pth"): LINK_PTH,
        os.path.join(site_packages, "_jazzoo_link.py"): LINK_MODULE.format(
            linked_dir=linked_dir
        ),
        os.path.join(dist_info, "METADATA"): METADATA.format(version=version),
        os.path.join(dist_info, "INSTALLER"): INSTALLER,
        os.path.join(dist_info, "entry_points.txt"): _entry_points(),
        os.path.join(dist_info, "direct_url.json"): _direct_url(linked_dir),
    }
    scripts = {
        os.path.join(venv_dir, "bin", name): SCRIPT.format(python=python, module=module)
        for name, module in CONSOLE_SCRIPTS.items()
    }

    # Remove what was written when a step fails, so that the venv is as it was
    written: T.List[str] = []
    try:
        os.makedirs(dist_info)
        written.append(dist_info)
        for path, text in {**files, **scripts}.items():
            with open(path, "x", encoding="utf-8") as f:
                written.append(path)
                f.write(text)
        for path in scripts:
            os.chmod(path, 0o755)
        _write_record(
            os.path.join(dist_info, "RECORD"), site_packages, {**files, **scripts}
        )
    except BaseException as error:
        for path in written:
            _remove(path)
        if isinstance(error, FileExistsError):
            raise JazzooLinkError(
                f"cannot link jazzoo into the venv {venv_dir}: "
                f"{error.filename} already exists"
            ) from error
        raise
    return written


def _remove(path: str):
    if os.path.islink(path) or os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)


def _entry_points() -> str:
    lines = [f"{name} = {module}:main" for name, module in CONSOLE_SCRIPTS.items()]
    return "[console_scripts]\n" + "\n".join(lines) + "\n"


def _direct_url(linked_dir: str) -> str:
    return json.dumps(
        {"url": Path(linked_dir).as_uri(), "dir_info": {"editable": True}}
    )


def _write_record(path: str, site_packages: str, files: T.Dict[str, str]) -> None:
    # pip uninstalls the files in RECORD, whose paths are relative to site-packages
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        for file_path, text in files.items():
            data = text.encode("utf-8")
            writer.writerow(
                [os.path.relpath(file_path, site_packages), _hash(data), len(data)]
            )
        writer.writerow([os.path.relpath(path, site_packages), "", ""])


def _hash(data: bytes) -> str:
    digest = hashlib.sha256(data).digest()
    return "sha256=" + base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def _inspect_python(python: str) -> T.Tuple[str, T.Tuple[int, int]]:
    try:
        completed = subprocess.run(
            [python, "-c", INSPECT_PYTHON],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        raise JazzooLinkError(f"could not run the python of the venv: {error}")
    if completed.returncode != 0:
        raise JazzooLinkError(
            f"could not run the python of the venv: {completed.stderr.strip()}"
        )
    info = json.loads(completed.stdout)
    return info["purelib"], tuple(info["version"][:2])


def _format_version(version: T.Tuple[int, ...]) -> str:
    return ".".join(str(part) for part in version)
