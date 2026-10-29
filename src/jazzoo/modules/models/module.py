import typing as T

from jazzoo.modules.models.scope import Scope
from jazzoo.utils.dataclass import dataclass


@dataclass
class Module(Scope):
    # Absolute path of the .jaz file this module was loaded from.
    filename: str = ""
    # Sub-modules keyed by the alias an *import* bound them to. This is the surface
    # a .jaz file can name: 🐭.ns.f() resolves through here.
    modules: T.List["Module"] = []
    # Export layers keyed by the alias an *export* bound them to (design section 9).
    # This is the surface the CLI can name: `jaz ns.f` resolves through here. The two
    # are kept apart so one alias can serve both without ambiguity.
    layers: T.List["Module"] = []
    name: str = ""
    # Where the import that bound this alias appears in the importing file, so a
    # name collision can point at whichever declaration came second.
    imported_at_line: T.Optional[int] = None
    # The 🐭 namespace: values assigned at module level, keyed by name.
    namespace: T.Dict[str, T.Any] = {}
    # False while the module's own top-level assignments are still running, which is
    # how a load-time circular reference is detected (design section 14).
    is_initialized: bool = False
    # The directory that jaz (or zoo) was called from. Only set on the root module.
    invocation_dir: str = ""
