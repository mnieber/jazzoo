import re
import typing as T

from jazzoo.blocks.actions.run_block import run_block
from jazzoo.enums import BlockMode, Sigil
from jazzoo.errors import ArgumentError
from jazzoo.expressions.rules.substitute_references import substitute_references
from jazzoo.expressions.utils.strip_one_newline import strip_one_newline
from jazzoo.functions.models.function import Function
from jazzoo.modules.models.frame import Frame
from jazzoo.modules.rules.parse_source import _ASSIGNMENT_RE, _SIGIL_TEXTS

# A whole line that is just `<sigil>.<path>(...)` - a mid-body call statement. No
# space is allowed before the parenthesis, so a shell line that merely contains a
# reference followed by a bracket is not mistaken for a call.
_STATEMENT_CALL_RE = re.compile(
    r"^(?:🐐|🐭|🐆|⚙️|⚙)\.[A-Za-z0-9_][A-Za-z0-9_.-]*\([^)]*\)$"
)


def bind_arguments(
    function: Function,
    arguments: T.Dict[str, str],
    filename: T.Optional[str] = None,
    line: T.Optional[int] = None,
) -> T.Dict[str, T.Any]:
    """Validate arguments against parameters and produce the 🐆 variables."""
    names = {p.name for p in function.parameters}
    for name in arguments:
        if name not in names:
            raise ArgumentError(
                f"{function.name}() has no parameter named '{name}'",
                filename=filename or function.filename,
                line=line if line is not None else function.line,
            )

    bound: T.Dict[str, T.Any] = {}
    for parameter in function.parameters:
        if parameter.name in arguments:
            bound[parameter.name] = arguments[parameter.name]
        elif parameter.default is not None:
            bound[parameter.name] = parameter.default
        else:
            raise ArgumentError(
                f"{function.name}() is missing a value for '{parameter.name}'",
                filename=filename or function.filename,
                line=line if line is not None else function.line,
            )
    return bound


def _echo(line_text: str, is_quiet: bool) -> None:
    # jazzoo prints each command so the caller can see what runs; `@` hides it.
    if not is_quiet:
        print(line_text)


def call_function(
    function: Function,
    arguments: T.Dict[str, str],
    frame: Frame,
    evaluate_expression: T.Callable,
    filename: T.Optional[str] = None,
    line: T.Optional[int] = None,
) -> str:
    """Run a function body and return its value.

    Every step sets the return value from its stdout, unless the body assigns
    🐆.retval explicitly - after which later blocks no longer change it.
    """
    call_frame = frame.child(module=function.module or frame.module)
    call_frame.locals.update(
        bind_arguments(function, arguments, filename=filename, line=line)
    )
    # Local functions defined in this body are callable by name within it.
    call_frame.local_functions = {f.name: f for f in function.functions}

    for dependency in function.dependencies:
        dependency_arguments = {
            argument.name: evaluate_expression(argument.value, call_frame)
            for argument in dependency.arguments
        }
        target = _lookup_function(dependency.target_path, call_frame, dependency)
        call_function(
            target,
            dependency_arguments,
            call_frame,
            evaluate_expression,
            filename=dependency.filename,
            line=dependency.line,
        )

    for block in function.body:
        _run_one_block(block, call_frame, evaluate_expression)

    if "retval" in call_frame.locals:
        return call_frame.locals["retval"]
    return strip_one_newline(call_frame.stdout)


def _lookup_function(path: str, frame: Frame, call_site) -> Function:
    from jazzoo.functions.rules.get_function_by_path import get_function_by_path
    from jazzoo.errors import ResolutionError

    local_functions = getattr(frame, "local_functions", {})
    if path in local_functions:
        return local_functions[path]

    function = get_function_by_path(frame.module, path)
    if function is None:
        raise ResolutionError(
            f"no such function: {path}",
            filename=getattr(call_site, "filename", None),
            line=getattr(call_site, "line", None),
        )
    return function


def _run_one_block(block, frame: Frame, evaluate_expression) -> None:
    """Sweep a block, then execute it.

    Sweeping walks the lines top to bottom: a jazzoo assignment is evaluated and
    removed, and every other line has its references substituted using the namespace
    state at that point. In jazzoo mode each remaining line is its own subprocess.
    """
    swept: T.List[T.Tuple[str, int, bool]] = []

    for block_line in block.lines:
        trimmed = block_line.text.strip()
        assignment = _ASSIGNMENT_RE.match(trimmed)
        if assignment:
            sigil = _SIGIL_TEXTS[assignment.group("sigil")]
            value = evaluate_expression(assignment.group("rhs").strip(), frame)
            frame.assign(sigil, assignment.group("name"), value)
            continue

        # A line that is nothing but a jazzoo call is a mid-body call, not a shell
        # line. Its return value is discarded, and it leaves ⚙️.stdout alone.
        if _STATEMENT_CALL_RE.match(trimmed):
            evaluate_expression(trimmed, frame)
            continue

        if block.mode == BlockMode.JAZZOO:
            # Each line is its own block, so it is substituted and run before the
            # next one is even looked at - which is what lets a line read the
            # ⚙️.output of the line above it.
            text = substitute_references(
                block_line.text,
                lambda reference: _resolve(reference, frame),
                filename=block.filename,
                line=block_line.line,
                evaluate_call=lambda call_text: _evaluate_call(call_text, frame),
            )
            _echo(text, block_line.is_quiet)
            frame.stdout = run_block(
                None, text, filename=block.filename, line=block_line.line
            )
            continue

        # A shebang block is one subprocess, so the whole block is swept first and
        # every line sees the namespace state as of its own position in the sweep.
        text = substitute_references(
            block_line.text,
            lambda reference: _resolve(reference, frame),
            filename=block.filename,
            line=block_line.line,
            evaluate_call=lambda call_text: _evaluate_call(call_text, frame),
        )
        swept.append((text, block_line.line, block_line.is_quiet))

    if not swept:
        return

    for text, _, is_quiet in swept:
        _echo(text, is_quiet)
    body = "\n".join(text for text, _, _ in swept)
    frame.stdout = run_block(
        block.shebang, body, filename=block.filename, line=swept[0][1]
    )


def _evaluate_call(call_text: str, frame: Frame) -> str:
    from jazzoo.expressions.actions.evaluate_expression import evaluate_call

    return evaluate_call(call_text, frame)


def _resolve(reference, frame: Frame) -> str:
    from jazzoo.expressions.rules.resolve_reference import resolve_reference

    return resolve_reference(reference, frame)
