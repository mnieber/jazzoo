import os
import subprocess
import sys

import jazzoo
from jazzoo.zoo.errors import VenvCreationError

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
    # follows the jazzoo that created it, e.g. a development checkout.
    python = os.path.join(venv_dir, "bin", "python")
    os.symlink(
        os.path.dirname(jazzoo.__file__),
        os.path.join(_site_packages_dir(python), "jazzoo"),
    )

    # The link has no package metadata, so pip would not create the scripts
    for name, module in CONSOLE_SCRIPTS.items():
        path = os.path.join(venv_dir, "bin", name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(SCRIPT.format(python=python, module=module))
        os.chmod(path, 0o755)


def _site_packages_dir(python: str) -> str:
    completed = subprocess.run(
        [python, "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip()
