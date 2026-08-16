import re
import typing as T

from jazzoo.errors import ArgumentError, ResolutionError
from jazzoo.functions.models.function import Function
from jazzoo.modules.models.module import Module
from jazzoo.modules.rules.parse_source import _ASSIGNMENT_RE, parse_call_arguments

# A call is only a call when it is the whole line, or the whole right-hand side of
# an assignment. Scanning shell text for anything call-shaped would misread
# `echo "Hello 🐆.who (tracing=🐭.tracing)"` as a call to `who`.
_CALL_RE = re.compile(
    r"^(?P<sigil>🐐|🐭|🐆|⚙️|⚙)\.(?P<path>[A-Za-z0-9_][A-Za-z0-9_.-]*)\((?P<args>[^)]*)\)$"
)


def validate_module(module: Module) -> None:
    """Check every call site in the module against the function it names.

    Raised at load time, before any subprocess runs, so a mistake in one target
    surfaces even when a different target is invoked.
    """
    for function in module.functions:
        _validate_function(function, module)


def _validate_function(function: Function, module: Module) -> None:
    for dependency in function.dependencies:
        _validate_call(
            dependency.target_path,
            [(a.name, a.value) for a in dependency.arguments],
            module,
            function,
            dependency.filename,
            dependency.line,
        )

    for block in function.body:
        for block_line in block.lines:
            trimmed = block_line.text.strip()
            assignment = _ASSIGNMENT_RE.match(trimmed)
            candidate = assignment.group("rhs").strip() if assignment else trimmed
            match = _CALL_RE.match(candidate)
            if match is None:
                continue
            arguments = parse_call_arguments(match.group("args"), None, None)
            _validate_call(
                match.group("path"),
                [(a.name, a.value) for a in arguments],
                module,
                function,
                block.filename,
                block_line.line,
            )

    for local in function.functions:
        _validate_function(local, module)


def _find_function(
    path: str, module: Module, enclosing: Function
) -> T.Optional[Function]:
    from jazzoo.functions.rules.get_function_by_path import get_function_by_path

    for local in enclosing.functions:
        if local.name == path:
            return local
    return get_function_by_path(module, path)


def _validate_call(
    path: str,
    arguments: T.List[T.Tuple[T.Optional[str], str]],
    module: Module,
    enclosing: Function,
    filename: T.Optional[str],
    line: T.Optional[int],
) -> None:
    target = _find_function(path, module, enclosing)
    if target is None:
        raise ResolutionError(
            f"no such function: {path}", filename=filename, line=line
        )

    for name, _ in arguments:
        if name is None:
            raise ArgumentError(
                f"arguments must be named in a .jaz file: {path}(...)",
                filename=filename,
                line=line,
            )

    supplied = {name for name, _ in arguments}
    declared = {p.name for p in target.parameters}
    for name in supplied:
        if name not in declared:
            raise ArgumentError(
                f"{target.name}() has no parameter named '{name}'",
                filename=filename,
                line=line,
            )
    for parameter in target.parameters:
        if parameter.default is None and parameter.name not in supplied:
            raise ArgumentError(
                f"{target.name}() is missing a value for '{parameter.name}'",
                filename=filename,
                line=line,
            )
