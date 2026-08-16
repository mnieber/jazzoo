import typing as T

from dataclassy import dataclass

from jazzoo.modules.models.scope import Scope


@dataclass
class Module(Scope):
    # Absolute path of the .jaz file this module was loaded from.
    filename: str = ""
    # Sub-modules keyed by the alias an import bound them to.
    modules: T.List["Module"] = []
    name: str = ""
    # The 🐭 namespace: values assigned at module level, keyed by name.
    namespace: T.Dict[str, T.Any] = {}
    # False while the module's own top-level assignments are still running, which is
    # how a load-time circular reference is detected (design section 14).
    is_initialized: bool = False
