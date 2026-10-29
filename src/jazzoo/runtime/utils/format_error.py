import os

from jazzoo.errors import JazzooError


def format_error(error: JazzooError) -> str:
    location = error.filename or ""
    if location and error.line is not None:
        location = f"{os.path.basename(location)}:{error.line}"
    elif location:
        location = os.path.basename(location)
    prefix = f"{location}: " if location else ""
    return f"{prefix}error: {error.message}"
