import contextlib
import re
import typing as T

from jazzoo.blocks.actions.run_block import run_block
from jazzoo.enums import BlockMode
from jazzoo.errors import JazzooError
from jazzoo.expressions.rules.substitute_references import substitute_references
from jazzoo.expressions.utils.strip_one_newline import strip_one_newline
from jazzoo.functions.actions.bind_arguments import bind_arguments
from jazzoo.functions.models.function import Function
from jazzoo.functions.rules.lookup_function import lookup_function
from jazzoo.modules.models.frame import Frame
from jazzoo.modules.rules.parse_source import _ASSIGNMENT_RE, _SIGIL_TEXTS

# A whole line that is just `<sigil>.<path>(...)` - a mid-body call statement. No
# space is allowed before the parenthesis, so a shell line that merely contains a
# reference followed by a bracket is not mistaken for a call.
_STATEMENT_CALL_RE = re.compile(
    r"^(?:🐐|🐭|🐆|⚙️|⚙)\.[A-Za-z0-9_][A-Za-z0-9_.-]*\([^)]*\)$"
)


def _echo(line_text: str, is_quiet: bool, frame: Frame) -> None:
    # jazzoo prints each command so the caller can see what runs; `@` hides it, and
    # so does a quiet call.
    if not is_quiet and not frame.is_quiet:
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
    # Defaults resolve in the defining module, before any parameter is bound.
    with call_frame.quietly():
        bound = bind_arguments(
            function,
            arguments,
            lambda source: evaluate_expression(source, call_frame),
            filename=filename,
            line=line,
        )
    call_frame.locals.update(bound)
    # Local functions defined in this body are callable by name within it.
    call_frame.local_functions = {f.name: f for f in function.functions}

    for dependency in function.dependencies:
        with call_frame.quietly():
            dependency_arguments = {
                argument.name: evaluate_expression(argument.value, call_frame)
                for argument in dependency.arguments
            }
        target = lookup_function(dependency.target_path, call_frame, dependency)
        call_function(
            target,
            dependency_arguments,
            call_frame,
            evaluate_expression,
            filename=dependency.filename,
            line=dependency.line,
        )

    for block in function.body:
        _run_one_block(block, call_frame, evaluate_expression, function.is_interactive)

    if "retval" in call_frame.locals:
        return call_frame.locals["retval"]
    return strip_one_newline(call_frame.stdout)


def _run_one_block(
    block, frame: Frame, evaluate_expression, is_interactive: bool
) -> None:
    """Sweep a block, then execute it.

    Sweeping walks the lines top to bottom: a jazzoo assignment is evaluated and
    removed, and every other line has its references substituted using the namespace
    state at that point. In jazzoo mode each remaining line is its own subprocess.
    """
    swept: T.List[T.Tuple[str, int]] = []

    for block_line in block.lines:
        trimmed = block_line.text.strip()
        assignment = _ASSIGNMENT_RE.match(trimmed)
        if assignment:
            sigil = _SIGIL_TEXTS[assignment.group("sigil")]
            with _located(block, block_line), frame.quietly():
                value = evaluate_expression(assignment.group("rhs").strip(), frame)
            frame.assign(sigil, assignment.group("name"), value)
            continue

        # A line that is nothing but a jazzoo call is a mid-body call, not a shell
        # line. Its return value is discarded, and it leaves ⚙️.stdout alone.
        if _STATEMENT_CALL_RE.match(trimmed):
            with _located(block, block_line):
                evaluate_expression(trimmed, frame)
            continue

        if block.mode == BlockMode.JAZZOO:
            # Each line is its own block, so it is substituted and run before the
            # next one is even looked at - which is what lets a line read the
            # ⚙️.output of the line above it.
            text = _sweep_line(block_line, block, frame)
            _echo(text, block_line.is_quiet, frame)
            frame.stdout = run_block(
                None,
                text,
                filename=block.filename,
                line=block_line.line,
                is_quiet=frame.is_quiet,
                is_interactive=is_interactive,
            )
            continue

        # A shebang block is one subprocess, so the whole block is swept first and
        # every line sees the namespace state as of its own position in the sweep.
        swept.append((_sweep_line(block_line, block, frame), block_line.line))

    if not swept:
        return

    # The swept body is a script rather than a command, so it is not echoed.
    body = "\n".join(text for text, _ in swept)
    frame.stdout = run_block(
        block.shebang,
        body,
        filename=block.filename,
        line=swept[0][1],
        is_quiet=frame.is_quiet,
        is_interactive=is_interactive,
    )


@contextlib.contextmanager
def _located(block, block_line) -> T.Iterator[None]:
    """Attribute an error that carries no source location to this body line."""
    try:
        yield
    except JazzooError as error:
        if error.filename is not None:
            raise
        raise type(error)(
            error.message, filename=block.filename, line=block_line.line
        ) from None


def _sweep_line(block_line, block, frame: Frame) -> str:
    return substitute_references(
        block_line.text,
        lambda reference: _resolve(reference, frame),
        filename=block.filename,
        line=block_line.line,
        evaluate_call=lambda call_text: _evaluate_call(call_text, frame),
        evaluate_braced=lambda source: _evaluate_braced(source, frame),
    )


def _evaluate_call(call_text: str, frame: Frame) -> T.Any:
    from jazzoo.expressions.actions.evaluate_call import evaluate_call

    # An inline call is substituted into the line, so its value is used.
    with frame.quietly():
        return evaluate_call(call_text, frame)


def _evaluate_braced(source: str, frame: Frame) -> T.Any:
    from jazzoo.expressions.actions.evaluate_expression import evaluate_expression

    with frame.quietly():
        return evaluate_expression(source, frame)


def _resolve(reference, frame: Frame) -> str:
    from jazzoo.expressions.rules.resolve_reference import resolve_reference

    return resolve_reference(reference, frame)
