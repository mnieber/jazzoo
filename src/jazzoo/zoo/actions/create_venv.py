import base64
import csv
import hashlib
import json
import os
import subprocess
import sys
import typing as T
from pathlib import Path

import jazzoo
from jazzoo.zoo.errors import VenvCreationError
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


def create_venv(venv_dir: str, prompt: str, with_pip: bool = True) -> None:
    args = [sys.executable, "-m", "venv", "--prompt", prompt]
    if not with_pip:
        args.append("--without-pip")
    completed = subprocess.run(
        [*args, venv_dir], stdin=subprocess.DEVNULL, capture_output=True, text=True
    )
    if completed.returncode != 0:
        raise VenvCreationError(
            f"could not create the venv {venv_dir}: {completed.stderr.strip()}"
        )

    # Jazzoo has no dependencies, so linking its package is enough. The venv then
    # follows the jazzoo that created it, e.g. a development checkout. The link is
    # a linked install that pip can uninstall without touching the linked directory.
    python = os.path.join(venv_dir, "bin", "python")
    site_packages = _site_packages_dir(python)
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

    os.makedirs(dist_info)
    for path, text in {**files, **scripts}.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    for path in scripts:
        os.chmod(path, 0o755)
    _write_record(
        os.path.join(dist_info, "RECORD"), site_packages, {**files, **scripts}
    )


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


def _site_packages_dir(python: str) -> str:
    completed = subprocess.run(
        [python, "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()
