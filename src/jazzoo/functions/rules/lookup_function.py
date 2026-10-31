from jazzoo.enums import Sigil
from jazzoo.functions.models.function import Function
from jazzoo.modules.models.frame import Frame


def lookup_function(path: str, frame: Frame, call_site=None) -> Function:
    from jazzoo.functions.rules.get_function_by_path import get_function_by_path
    from jazzoo.errors import ResolutionError

    local_functions = getattr(frame, "local_functions", {})
    if path in local_functions:
        return local_functions[path]

    # A variable may hold a function; calling it calls what it holds.
    if "." not in path:
        from jazzoo.functions.models.curried_function import CurriedFunction

        for sigil in (Sigil.LEOPARD, Sigil.MOUSE, Sigil.GOAT):
            held = frame.lookup(sigil, path)
            if isinstance(held, CurriedFunction):
                return held.function

    function = get_function_by_path(frame.module, path)
    if function is None:
        raise ResolutionError(
            f"no such function: {path}",
            filename=getattr(call_site, "filename", None),
            line=getattr(call_site, "line", None),
        )

    # A circular import hands back the cached, partially-initialized module. Using
    # it at call time is fine; reaching it while it is still loading is not, because
    # its own top-level assignments have not run yet (design section 14).
    owner = function.module
    if owner is not None and not owner.is_initialized and owner is not frame.module:
        from jazzoo.errors import ModuleImportError

        raise ModuleImportError(
            f"'{path}' is not available yet: {owner.name} is still loading",
            filename=getattr(call_site, "filename", None),
            line=getattr(call_site, "line", None),
        )

    return function
