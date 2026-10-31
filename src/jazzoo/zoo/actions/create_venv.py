import subprocess
import sys

from jazzoo.zoo.actions.link_jazzoo import link_jazzoo
from jazzoo.zoo.errors import VenvCreationError


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

    link_jazzoo(venv_dir)
