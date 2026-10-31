import typing as T

from jazzoo.enums import Sigil
from jazzoo.errors import ParseError
from jazzoo.modules.models.module import Module


def check_name_collisions(parsed, module: Module) -> None:
    """A name denotes one of a variable, a function or a namespace - never two.

    A reference names only a sigil and a name, so `🐭.foo` does not say which to look
    in (design section 13). Only the first segment of a dotted name is checked, since
    that is what names something in this scope: `🐭.docker.build` collides with a
    `docker` namespace but not with a module-level `build`.
    """
    # Every declaration this scope makes, as (line, name), so the error can point at
    # whichever of a colliding pair came second in the file.
    declarations: T.List[T.Tuple[int, str]] = []

    for function in module.functions:
        # A function bound by an import or export is declared by that statement.
        line = function.bound_at_line or function.line
        declarations.append((line or 0, function.name))

    for child in module.modules:
        declarations.append((child.imported_at_line or 0, child.name))

    # A variable may be assigned more than once - `🐭.cfg = "x"` then
    # `🐭.cfg.name = "y"` is a re-assignment, not a redeclaration - so each variable
    # contributes one declaration, at the line it first appears.
    first_assignment: T.Dict[str, int] = {}
    for assignment in parsed.assignments:
        if assignment.sigil is not Sigil.MOUSE:
            continue
        # Only the first segment names something in this scope.
        name = assignment.name.split(".")[0]
        first_assignment.setdefault(name, assignment.line or 0)
    declarations.extend((line, name) for name, line in first_assignment.items())

    seen: T.Set[str] = set()
    for line, name in sorted(declarations):
        if name in seen:
            raise ParseError(
                f"'{name}' is already defined in this scope",
                filename=module.filename,
                line=line,
            )
        seen.add(name)
