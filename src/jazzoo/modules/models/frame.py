import typing as T

from jazzoo.enums import Sigil
from jazzoo.modules.models.absent import ABSENT


class Frame:
    """The namespace state a line is evaluated against.

    Holds the 🐆 locals of the running invocation plus ⚙️.stdout, and points at the
    module the line lives in (🐭, ⚙️.module) and the entry-point module
    (⚙️.root_module). 🐐 globals live in a single dict shared by the whole run.
    """

    def __init__(
        self,
        module,
        root_module,
        globals_: T.Dict[str, T.Any],
        locals_: T.Optional[T.Dict[str, T.Any]] = None,
    ):
        self.module = module
        self.root_module = root_module
        self.globals = globals_
        self.locals: T.Dict[str, T.Any] = {} if locals_ is None else locals_
        self.stdout = ""

    def lookup(self, sigil: Sigil, name: str) -> T.Any:
        if sigil is Sigil.GOAT:
            return self.globals.get(name, ABSENT)
        if sigil is Sigil.LEOPARD:
            return self.locals.get(name, ABSENT)
        if sigil is Sigil.MOUSE:
            return self.module.namespace.get(name, ABSENT)
        return ABSENT

    def assign(self, sigil: Sigil, name: str, value: T.Any) -> None:
        if sigil is Sigil.GOAT:
            self.globals[name] = value
        elif sigil is Sigil.LEOPARD:
            self.locals[name] = value
        elif sigil is Sigil.MOUSE:
            self.module.namespace[name] = value

    def child(self, module=None) -> "Frame":
        """A fresh frame for a callee: new 🐆 scope and its own ⚙️.stdout."""
        return Frame(
            module=module or self.module,
            root_module=self.root_module,
            globals_=self.globals,
        )
