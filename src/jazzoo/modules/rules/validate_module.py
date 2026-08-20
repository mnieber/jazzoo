import re
import typing as T

from jazzoo.enums import Sigil
from jazzoo.errors import ArgumentError, ParseError, ResolutionError
from jazzoo.functions.models.function import Function
from jazzoo.modules.models.module import Module
from jazzoo.modules.rules.parse_source import (
    _ASSIGNMENT_RE,
    _SIGIL_TEXTS,
    parse_call_arguments,
)

# A call is only a call when it is the whole line, or the whole right-hand side of
# an assignment. Scanning shell text for anything call-shaped would misread
# `echo "Hello 🐆.who (tracing=🐭.tracing)"` as a call to `who`.
_CALL_RE = re.compile(
    r"^(?P<sigil>🐐|🐭|🐆|⚙️|⚙)\.(?P<path>[A-Za-z0-9_][A-Za-z0-9_.-]*)\((?P<args>[^)]*)\)$"
)


def validate_module(
    module: Module, function_valued: T.Optional[T.Dict[str, Function]] = None
) -> None:
    """Check every call site in the module against the function it names.

    Raised at load time, before any subprocess runs, so a mistake in one target
    surfaces even when a different target is invoked.

    `function_valued` maps module-level variables that hold a function to the
    function they hold, so a call through a curried name resolves.
    """
    for function in module.functions:
        _validate_function(function, module, function_valued or {})


def _validate_function(
    function: Function, module: Module, function_valued: T.Dict[str, Function]
) -> None:
    for dependency in function.dependencies:
        _validate_call(
            dependency.target_path,
            [(a.name, a.value) for a in dependency.arguments],
            module,
            function,
            dependency.filename,
            dependency.line,
            function_valued,
        )

    # A body may assign a function to a 🐆 variable and then call through it, so
    # those names are collected before the calls in this body are checked.
    in_scope = dict(function_valued)
    in_scope.update(_function_valued_locals(function, module, function_valued))

    for block in function.body:
        for block_line in block.lines:
            trimmed = block_line.text.strip()
            assignment = _ASSIGNMENT_RE.match(trimmed)
            if assignment is not None:
                # ⚙️ is read-only everywhere, including inside a body. Bodies are
                # opaque to the parser, so the check belongs here rather than in
                # parse_source.
                if _SIGIL_TEXTS[assignment.group("sigil")] is Sigil.SYSTEM:
                    raise ParseError(
                        "cannot assign to the read-only ⚙️ namespace",
                        filename=block.filename,
                        line=block_line.line,
                    )
            candidate = assignment.group("rhs").strip() if assignment else trimmed
            if assignment is not None:
                # An unquoted string on the right-hand side is a ParseError, and is
                # decidable from the source alone.
                _validate_expression(
                    candidate, block.filename, block_line.line
                )
            _validate_pipes(
                candidate, module, in_scope, block.filename, block_line.line
            )
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
                in_scope,
            )

    for local in function.functions:
        _validate_function(local, module, in_scope)


def _function_valued_locals(
    function: Function, module: Module, outer: T.Dict[str, Function]
) -> T.Dict[str, T.Any]:
    """🐆 variables in this body that hold a function, keyed by name."""
    from jazzoo.expressions.rules.parse_expression import (
        Curry,
        ReferenceText,
        parse_expression,
    )
    from jazzoo.expressions.rules.split_reference_path import split_reference_path
    from jazzoo.functions.rules.get_function_by_path import get_function_by_path
    from jazzoo.functions.rules.parse_curry import parse_curry

    found: T.Dict[str, T.Any] = {}
    for block in function.body:
        for block_line in block.lines:
            assignment = _ASSIGNMENT_RE.match(block_line.text.strip())
            if assignment is None:
                continue
            try:
                node = parse_expression(assignment.group("rhs").strip())
            except Exception:
                continue

            alternatives = _boolean_operand_functions(node, module, {**outer, **found})
            if alternatives is not None:
                if alternatives:
                    # The value is one of several functions, decided at run time, so
                    # record every candidate rather than a single guess.
                    found[assignment.group("name")] = _Alternatives(
                        functions=alternatives
                    )
                continue

            if isinstance(node, Curry):
                target_text, brackets = node.target.text, node.text
            elif isinstance(node, ReferenceText):
                target_text, brackets = node.text, "[]"
            else:
                continue

            split = split_reference_path(target_text)
            if split is None:
                continue
            path = split[1]

            held = outer.get(path) or found.get(path)
            target = (
                held.function if held is not None
                else get_function_by_path(module, path)
            )
            if target is None:
                continue
            found[assignment.group("name")] = parse_curry(
                target, brackets, filename=block.filename, line=block_line.line
            )
    return found


def _validate_expression(
    source: str, filename: T.Optional[str], line: T.Optional[int]
) -> None:
    """Parse an expression so its parse-time errors surface at load time."""
    from jazzoo.expressions.rules.parse_expression import parse_expression

    try:
        parse_expression(source)
    except ParseError as error:
        raise ParseError(
            error.message, filename=filename, line=line
        ) from None


def _validate_pipes(
    source: str,
    module: Module,
    function_valued: T.Dict[str, Function],
    filename: T.Optional[str],
    line: T.Optional[int],
) -> None:
    """Check that each pipe stage leaves exactly one parameter unbound.

    Which parameter is free must be decidable from the expression alone, so a stage
    binding all of them, or leaving two, is an ArgumentError at parse time.
    """
    from jazzoo.expressions.models.pipe import Pipe
    from jazzoo.expressions.rules.parse_expression import (
        Curry,
        ReferenceText,
        parse_expression,
    )
    from jazzoo.expressions.rules.split_reference_path import split_reference_path
    from jazzoo.functions.rules.get_function_by_path import get_function_by_path
    from jazzoo.functions.rules.parse_curry import get_free_parameters, parse_curry

    if "|" not in source:
        return
    try:
        node = parse_expression(source)
    except Exception:
        return
    if not isinstance(node, Pipe):
        return

    for stage in node.stages:
        if isinstance(stage, Curry):
            target_text, brackets = stage.target.text, stage.text
        elif isinstance(stage, ReferenceText):
            target_text, brackets = stage.text, "[]"
        else:
            continue

        split = split_reference_path(target_text)
        if split is None:
            continue
        sigil, path = split
        if sigil is Sigil.SYSTEM:
            # A built-in operator, not a user function.
            continue

        held = function_valued.get(path)
        target = held.function if held is not None else get_function_by_path(module, path)
        if target is None:
            continue

        curried = parse_curry(target, brackets, filename=filename, line=line)
        if held is not None and brackets == "[]":
            # Piping a variable that already holds a curry keeps its bindings.
            curried = held
        free = get_free_parameters(curried)
        if len(free) != 1:
            raise ArgumentError(
                f"a pipe stage must leave exactly one parameter unbound; "
                f"{target.name}() leaves {len(free)}",
                filename=filename,
                line=line,
            )


def _find_function(
    path: str,
    module: Module,
    enclosing: Function,
    function_valued: T.Dict[str, Function],
) -> T.Optional[Function]:
    from jazzoo.functions.rules.get_function_by_path import get_function_by_path

    for local in enclosing.functions:
        if local.name == path:
            return local
    if path in function_valued:
        return function_valued[path].function
    return get_function_by_path(module, path)


class _Alternatives:
    """A name that holds one of several functions, chosen at run time.

    It resolves - the name is callable - but its arguments can only be checked
    against the set, since which member is called is not decidable here.
    """

    def __init__(self, functions: T.List[Function]):
        self.functions = functions
        # Enough of the CurriedFunction shape for the call path to treat it alike.
        self.function = functions[0]
        self.bound: T.Dict[str, str] = {}
        self.explicitly_unbound: T.List[str] = []


def _validate_call(
    path: str,
    arguments: T.List[T.Tuple[T.Optional[str], str]],
    module: Module,
    enclosing: Function,
    filename: T.Optional[str],
    line: T.Optional[int],
    function_valued: T.Dict[str, Function],
) -> None:
    held_alternatives = function_valued.get(path)
    if isinstance(held_alternatives, _Alternatives):
        _validate_against_alternatives(
            held_alternatives, path, arguments, filename, line
        )
        return

    target = _find_function(path, module, enclosing, function_valued)
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
    held = function_valued.get(path)
    if held is not None:
        for name in supplied:
            if name in held.bound:
                raise ArgumentError(
                    f"{target.name}() already has a value for '{name}' from currying",
                    filename=filename,
                    line=line,
                )
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


def _boolean_operand_functions(
    node: T.Any, module: Module, known: T.Dict[str, T.Any]
) -> T.Optional[T.List[Function]]:
    """Every function a boolean expression could yield, or None if it is not one.

    `and` and `or` yield one of their operands, and which one is a run-time
    question. Collecting them all lets a call through such a name be accepted when
    *any* operand would accept it, rather than guessing a single representative and
    rejecting calls the other operand would have allowed.
    """
    from jazzoo.expressions.models.boolean import And, Or
    from jazzoo.expressions.rules.parse_expression import Curry, ReferenceText
    from jazzoo.expressions.rules.split_reference_path import split_reference_path
    from jazzoo.functions.rules.get_function_by_path import get_function_by_path

    if not isinstance(node, (And, Or)):
        return None

    found: T.List[Function] = []
    pending = [node]
    while pending:
        current = pending.pop()
        if isinstance(current, (And, Or)):
            pending.extend([current.left, current.right])
            continue
        if isinstance(current, Curry):
            current = current.target
        if not isinstance(current, ReferenceText):
            continue
        split = split_reference_path(current.text)
        if split is None:
            continue
        path = split[1]
        held = known.get(path)
        function = (
            held.function if held is not None
            else get_function_by_path(module, path)
        )
        if function is not None:
            found.append(function)
    return found


def _validate_against_alternatives(
    held: "_Alternatives",
    path: str,
    arguments: T.List[T.Tuple[T.Optional[str], str]],
    filename: T.Optional[str],
    line: T.Optional[int],
) -> None:
    """Accept the call when any candidate would accept it.

    Rejecting on one candidate would flag calls that are correct for the operand
    actually chosen, so only a call that no candidate could satisfy is an error.
    """
    for name, _ in arguments:
        if name is None:
            raise ArgumentError(
                f"arguments must be named in a .jaz file: {path}(...)",
                filename=filename,
                line=line,
            )

    supplied = {name for name, _ in arguments}
    for function in held.functions:
        declared = {p.name for p in function.parameters}
        if not supplied <= declared:
            continue
        missing = [
            p.name
            for p in function.parameters
            if p.default is None and p.name not in supplied
        ]
        if not missing:
            return

    names = " or ".join(sorted({f.name for f in held.functions}))
    raise ArgumentError(
        f"no function {path} could be called with these arguments ({names})",
        filename=filename,
        line=line,
    )
