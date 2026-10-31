import os
import typing as T

from jazzoo.modules.actions.load_module import load_module
from jazzoo.modules.models.module import Module

# 🐐 is shared by every module in a run.
_GLOBALS: T.Dict[str, T.Any] = {}


def parse_module(
    path: str, invocation_dir: T.Optional[str] = None, run_statements: bool = True
) -> Module:
    """Load a .jaz file: parse it, wire its imports, validate it, and run its
    top-level assignments.

    Everything decidable from the parse tree is raised here rather than when a
    target runs (design section 12), so a bad call site fails even if a different
    target is invoked. Note that loading also *executes*: a top-level assignment
    may call a function whose body is a shebang block, and a top-level ⚙️.load_env
    changes the environment. With run_statements=False, the statements do not run,
    so that the targets can be inspected without side effects.
    """
    _GLOBALS.clear()
    cache: T.Dict[str, Module] = {}
    return load_module(
        os.path.abspath(path),
        cache,
        root=None,
        globals_=_GLOBALS,
        invocation_dir=invocation_dir or os.getcwd(),
        run_statements=run_statements,
    )
