import os
import typing as T

from jazzoo.enums import Sigil
from jazzoo.errors import ResolutionError
from jazzoo.expressions.models.reference import Reference
from jazzoo.expressions.rules.get_by_path import get_by_path
from jazzoo.expressions.utils.strip_one_newline import strip_one_newline
from jazzoo.modules.models.absent import ABSENT


def _system_value(reference: Reference, context) -> T.Any:
    parts = reference.parts

    if parts[0] == "env":
        if len(parts) != 2:
            return ABSENT
        return os.environ.get(parts[1], ABSENT)

    if parts[0] == "stdout":
        return context.stdout
    if parts[0] == "output":
        return strip_one_newline(context.stdout)

    if parts[0] in ("module", "root_module") and len(parts) == 2:
        module = context.module if parts[0] == "module" else context.root_module
        path = module.filename
        if parts[1] == "path":
            return path
        if parts[1] == "basename":
            return os.path.basename(path)
        if parts[1] == "dirname":
            return os.path.dirname(path)

    return ABSENT


def resolve_reference(reference: Reference, context) -> T.Any:
    """Resolve one reference against the current namespace state.

    A dotted name walks into a structured value: the first segment names the
    variable and the rest is a path into it. Honours the `?` marker (absent
    resolves to "") and the `:-` marker (a default used when the value is empty).
    """
    if reference.sigil is Sigil.SYSTEM:
        value = _system_value(reference, context)
    else:
        value = context.lookup(reference.sigil, reference.parts[0])
        if value is not ABSENT and len(reference.parts) > 1:
            value = get_by_path(value, reference.parts[1:])

    if value is ABSENT:
        if reference.default is not None and reference.is_optional:
            return reference.default
        if reference.is_optional:
            return ""
        raise ResolutionError(
            f"{reference.sigil.value}.{reference.name} is not defined",
            filename=reference.filename,
            line=reference.line,
        )

    if value == "" and reference.default is not None:
        return reference.default
    return value
