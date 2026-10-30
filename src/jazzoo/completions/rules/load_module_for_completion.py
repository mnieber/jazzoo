import os
import typing as T

from jazzoo.errors import JazzooError
from jazzoo.modules.actions.parse_module import parse_module
from jazzoo.modules.models.module import Module
from jazzoo.settings import DEFAULT_FILENAMES


def load_module_for_completion(
    filename: T.Optional[str], root_dir: str
) -> T.Optional[Module]:
    if filename is None:
        filename = next(
            (
                os.path.join(root_dir, name)
                for name in DEFAULT_FILENAMES
                if os.path.exists(os.path.join(root_dir, name))
            ),
            None,
        )
    if filename is None:
        return None

    # A completion must not have side effects, so the statements do not run
    try:
        return parse_module(filename, run_statements=False)
    except (JazzooError, OSError):
        return None
