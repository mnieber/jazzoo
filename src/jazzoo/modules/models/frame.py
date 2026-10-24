import contextlib
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
        # Set while a call's return value is being computed for a caller that uses
        # it. A quiet frame echoes no commands and forwards no stdout.
        self.is_quiet = False

    def lookup(self, sigil: Sigil, name: str) -> T.Any:
        if sigil is Sigil.GOAT:
            return self.globals.get(name, ABSENT)
        if sigil is Sigil.LEOPARD:
            if name == "retval" and "retval" not in self.locals:
                # Until the body assigns it, 🐆.retval has no value of its own and
                # falls back to ⚙️.output (design section 384).
                from jazzoo.expressions.utils.strip_one_newline import (
                    strip_one_newline,
                )

                return strip_one_newline(self.stdout)
            return self.locals.get(name, ABSENT)
        if sigil is Sigil.MOUSE:
            return self.module.namespace.get(name, ABSENT)
        return ABSENT

    def _namespace_for(self, sigil: Sigil) -> T.Optional[T.Dict[str, T.Any]]:
        if sigil is Sigil.GOAT:
            return self.globals
        if sigil is Sigil.LEOPARD:
            return self.locals
        if sigil is Sigil.MOUSE:
            return self.module.namespace
        return None

    def assign(self, sigil: Sigil, name: str, value: T.Any) -> None:
        """Assign a value, creating intermediate objects for a dotted name."""
        from jazzoo.expressions.rules.get_by_path import set_by_path

        namespace = self._namespace_for(sigil)
        if namespace is None:
            return
        set_by_path(namespace, name.split("."), value)

    def child(self, module=None) -> "Frame":
        """A fresh frame for a callee: new 🐆 scope and its own ⚙️.stdout."""
        child = Frame(
            module=module or self.module,
            root_module=self.root_module,
            globals_=self.globals,
        )
        # Everything a quiet call runs is quiet too.
        child.is_quiet = self.is_quiet
        return child

    @contextlib.contextmanager
    def quietly(self) -> T.Iterator["Frame"]:
        """Evaluate calls whose value is used without printing what they run."""
        was_quiet = self.is_quiet
        self.is_quiet = True
        try:
            yield self
        finally:
            self.is_quiet = was_quiet
