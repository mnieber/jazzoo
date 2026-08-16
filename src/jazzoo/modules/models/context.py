import typing as T

from dataclassy import dataclass

from jazzoo.modules.models.module import Module

if T.TYPE_CHECKING:
    from jazzoo.modules.models.scope import Scope


@dataclass
class Context:
    # The module the executing line lives in - what 🐭 and ⚙️.module resolve against.
    module: Module
    # The entry-point module for the whole run - what ⚙️.root_module resolves against.
    root_module: Module
    # The 🐆 scope of the running function invocation, or None at module level.
    function_scope: T.Optional["Scope"] = None
    # Raw stdout of the last block in the current function; ⚙️.output trims it.
    stdout: str = ""
