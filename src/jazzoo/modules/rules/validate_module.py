import re
import typing as T

from jazzoo.enums import Sigil
from jazzoo.errors import ArgumentError, ParseError, ResolutionError
from jazzoo.functions.models.function import Function
from jazzoo.modules.models.module import Module
from jazzoo.modules.rules.parse_call_arguments import parse_call_arguments
from jazzoo.modules.rules.parse_source import _ASSIGNMENT_RE, _SIGIL_TEXTS

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
        if function.module is not None and function.module is not module:
            # An imported or exported function resolves its calls in the module
            # that defines it, and was validated when that module was loaded.
            continue
        _validate_function(function, module, function_valued or {})


def validate_builtin_call(
    name: str,
    arguments: T.List[T.Tuple[T.Optional[str], str]],
    filename: T.Optional[str],
    line: T.Optional[int],
) -> None:
    """Check a call to a ⚙️ function against its parameters."""
    from jazzoo.functions.actions.call_builtin_function import BUILTIN_PARAMETERS

    parameters = BUILTIN_PARAMETERS.get(name)
    if parameters is None:
        raise ResolutionError(
            f"no such function: ⚙️.{name}", filename=filename, line=line
        )
    _validate_arguments(
        f"⚙️.{name}", f"⚙️.{name}", parameters, arguments, filename, line
    )


def _validate_function(
    function: Function, module: Module, function_valued: T.Dict[str, Function]
) -> None:
    # A default is an expression, so an unquoted string in it is a ParseError.
    for parameter in function.parameters:
        if parameter.default is not None:
            _validate_expression(parameter.default, function.filename, function.line)

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
            _validate_braced_expressions(
                block_line.text, block.filename, block_line.line
            )
            candidate = assignment.group("rhs").strip() if assignment else trimmed
            if assignment is not None:
                # An unquoted string on the right-hand side is a ParseError, and is
                # decidable from the source alone.
                _validate_expression(candidate, block.filename, block_line.line)
            _validate_pipes(
                candidate, module, in_scope, block.filename, block_line.line
            )
            match = _CALL_RE.match(candidate)
            if match is None:
                continue
            arguments = parse_call_arguments(match.group("args"), None, None)
            if _SIGIL_TEXTS[match.group("sigil")] is Sigil.SYSTEM:
                validate_builtin_call(
                    match.group("path"),
                    [(a.name, a.value) for a in arguments],
                    block.filename,
                    block_line.line,
                )
                continue
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

            collected = _boolean_operand_functions(node, module, {**outer, **found})
            if collected is not None:
                functions, not_functions = collected
                if functions:
                    # One of several values, decided at run time. Assigning it is
                    # fine; whether it can be *called* is settled at the call site.
                    found[assignment.group("name")] = _Alternatives(
                        functions=functions, not_functions=not_functions
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
                held.function
                if held is not None
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
        raise ParseError(error.message, filename=filename, line=line) from None


def _validate_braced_expressions(
    text: str, filename: T.Optional[str], line: T.Optional[int]
) -> None:
    """Parse the expressions written between braces in a body line."""
    from jazzoo.expressions.rules.parse_references import parse_references

    for match in parse_references(text, filename=filename, line=line):
        if match.expression_text is not None:
            _validate_expression(match.expression_text, filename, line)


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
        target = (
            held.function if held is not None else get_function_by_path(module, path)
        )
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

    def __init__(self, functions: T.List[Function], not_functions: T.List[str]):
        self.functions = functions
        # Operands that name no function. Harmless until the value is called.
        self.not_functions = not_functions
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
        raise ResolutionError(f"no such function: {path}", filename=filename, line=line)

    held = function_valued.get(path)
    if held is not None:
        for name, _ in arguments:
            if name in held.bound:
                raise ArgumentError(
                    f"{target.name}() already has a value for '{name}' from currying",
                    filename=filename,
                    line=line,
                )
    _validate_arguments(path, target.name, target.parameters, arguments, filename, line)


def _validate_arguments(
    path: str,
    name: str,
    parameters,
    arguments: T.List[T.Tuple[T.Optional[str], str]],
    filename: T.Optional[str],
    line: T.Optional[int],
) -> None:
    for argument_name, _ in arguments:
        if argument_name is None:
            raise ArgumentError(
                f"arguments must be named in a .jaz file: {path}(...)",
                filename=filename,
                line=line,
            )

    supplied = {argument_name for argument_name, _ in arguments}
    declared = {p.name for p in parameters}
    for argument_name in supplied:
        if argument_name not in declared:
            raise ArgumentError(
                f"{name}() has no parameter named '{argument_name}'",
                filename=filename,
                line=line,
            )
    for parameter in parameters:
        if parameter.default is None and parameter.name not in supplied:
            raise ArgumentError(
                f"{name}() is missing a value for '{parameter.name}'",
                filename=filename,
                line=line,
            )


def _boolean_operand_functions(
    node: T.Any, module: Module, known: T.Dict[str, T.Any]
) -> T.Optional[T.Tuple[T.List[Function], T.List[str]]]:
    """Every function a boolean expression could yield, or None if it is not one.

    `and` and `or` yield one of their operands, and which one is a run-time
    question. Collecting them all lets the call be checked against every function it
    could reach, so a call site is only accepted when it is correct whichever
    operand wins.

    Operands that do not name a function are reported alongside the ones that do,
    because a name is only safely callable when *every* branch yields a function.
    The check itself belongs to the call site: assigning such a value is fine, and
    only calling through it is an error.
    """
    from jazzoo.expressions.models.boolean import And, Or
    from jazzoo.expressions.rules.parse_expression import Curry, ReferenceText
    from jazzoo.expressions.rules.split_reference_path import split_reference_path
    from jazzoo.functions.rules.get_function_by_path import get_function_by_path

    if not isinstance(node, (And, Or)):
        return None

    found: T.List[Function] = []
    not_functions: T.List[str] = []
    pending = [node]
    while pending:
        current = pending.pop()
        if isinstance(current, (And, Or)):
            pending.extend([current.left, current.right])
            continue
        if isinstance(current, Curry):
            current = current.target
        if not isinstance(current, ReferenceText):
            # A literal operand - a string or number - can never be called.
            not_functions.append(_operand_label(current))
            continue
        split = split_reference_path(current.text)
        if split is None:
            not_functions.append(current.text)
            continue
        path = split[1]
        held = known.get(path)
        function = (
            held.function if held is not None else get_function_by_path(module, path)
        )
        if function is not None:
            found.append(function)
        else:
            not_functions.append(current.text)
    return found, not_functions


def _operand_label(node: T.Any) -> str:
    """How a non-reference operand is named in an error message."""
    text = getattr(node, "text", None)
    if text is not None:
        return f'"{text}"'
    return str(getattr(node, "value", node))


def _validate_against_alternatives(
    held: "_Alternatives",
    path: str,
    arguments: T.List[T.Tuple[T.Optional[str], str]],
    filename: T.Optional[str],
    line: T.Optional[int],
) -> None:
    """Require every candidate to accept the call.

    Which candidate runs is decided at run time, so demanding that all of them
    accept is what makes the call correct whichever one wins. Checking only that
    *some* candidate accepts would make a boolean-valued name looser than a plain
    one, which is the opposite of what load-time checking is for.
    """
    if held.not_functions:
        # Some branch yields a value that cannot be called at all, so the call is
        # wrong whenever that branch wins.
        names = ", ".join(sorted(set(held.not_functions)))
        raise ParseError(
            f"{path} cannot always be called: {names} is not a function",
            filename=filename,
            line=line,
        )

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
        for name in sorted(supplied - declared):
            raise ArgumentError(
                f"{function.name}() has no parameter named '{name}'",
                filename=filename,
                line=line,
            )
        for parameter in function.parameters:
            if parameter.default is None and parameter.name not in supplied:
                raise ArgumentError(
                    f"{function.name}() is missing a value for " f"'{parameter.name}'",
                    filename=filename,
                    line=line,
                )
