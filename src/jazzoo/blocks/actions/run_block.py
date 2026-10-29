import os
import stat
import subprocess
import sys
import tempfile
import typing as T

from jazzoo.errors import ExecutionError
from jazzoo.settings import DEFAULT_SHEBANG


def run_block(
    shebang: T.Optional[str],
    body: str,
    filename: T.Optional[str] = None,
    line: T.Optional[int] = None,
    is_quiet: bool = False,
    is_interactive: bool = False,
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

        if is_interactive:
            # Whatever was echoed must reach the console before the block's output
            sys.stdout.flush()
            sys.stderr.flush()
            completed = subprocess.run([handle.name])
        else:
            completed = subprocess.run(
                [handle.name],
                capture_output=True,
                text=True,
            )
    finally:
        os.unlink(handle.name)

    # An interactive block writes to the console itself, and Jazzoo never sees its
    # output, not even in a quiet call.
    if is_interactive:
        if completed.returncode != 0:
            raise ExecutionError(
                f"recipe failed with exit code {completed.returncode}: "
                f"command failed: {body.strip()}",
                filename=filename,
                line=line,
            )
        return ""

    # The block's own output goes to the console as well as being captured for
    # ⚙️.stdout, so a target behaves like the commands it runs. A quiet block keeps
    # its stdout for the caller, but its stderr is always shown.
    if completed.stdout and not is_quiet:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)

    if completed.returncode != 0:
        message = completed.stderr.strip() or f"command failed: {body.strip()}"
        raise ExecutionError(
            f"recipe failed with exit code {completed.returncode}: {message}",
            filename=filename,
            line=line,
        )

    return completed.stdout
