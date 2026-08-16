import logging
import os
import stat
import subprocess
import tempfile
import typing as T

from jazzoo.errors import ExecutionError
from jazzoo.settings import DEFAULT_SHEBANG

logger = logging.getLogger(__name__)


def run_block(
    shebang: T.Optional[str],
    body: str,
    filename: T.Optional[str] = None,
    line: T.Optional[int] = None,
) -> str:
    """Run one block as a single subprocess and return its raw stdout.

    The block is written to a temporary executable file so the shebang selects the
    interpreter, exactly as it would for a script on disk.
    """
    shebang = shebang or DEFAULT_SHEBANG
    script = shebang + "\n" + body
    if not script.endswith("\n"):
        script += "\n"

    handle = tempfile.NamedTemporaryFile(
        mode="w", suffix=".jaz-block", delete=False, encoding="utf-8"
    )
    try:
        handle.write(script)
        handle.close()
        os.chmod(handle.name, os.stat(handle.name).st_mode | stat.S_IEXEC)

        completed = subprocess.run(
            [handle.name],
            capture_output=True,
            text=True,
        )
    finally:
        os.unlink(handle.name)

    if completed.stderr:
        logger.debug("block stderr: %s", completed.stderr.rstrip())

    if completed.returncode != 0:
        message = completed.stderr.strip() or f"command failed: {body.strip()}"
        raise ExecutionError(
            f"recipe failed with exit code {completed.returncode}: {message}",
            filename=filename,
            line=line,
        )

    return completed.stdout
