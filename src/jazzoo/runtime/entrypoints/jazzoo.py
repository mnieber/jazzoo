import argparse
import os
import sys
import traceback
import typing as T

from jazzoo.errors import ArgumentError, JazzooError
from jazzoo.settings import DEFAULT_FILENAMES


def _parse_args(argv: T.Optional[T.List[str]] = None):
    parser = argparse.ArgumentParser(
        prog="jaz", description="Run targets from a .jaz file.", add_help=False
    )
    parser.add_argument("--file", dest="file", default=None)
    parser.add_argument("--list", dest="list_targets", action="store_true")
    parser.add_argument("--trace", dest="trace", action="store_true")
    parser.add_argument("--help", "-h", dest="help", action="store_true")
    parser.add_argument("rest", nargs="*")
    return parser.parse_args(argv)


def _find_default_file() -> str:
    """The default file is `jazzoo`, falling back to `jazzoo.jaz`."""
    for name in DEFAULT_FILENAMES:
        if os.path.exists(name):
            return name
    raise JazzooError(
        "no jazzoo file found; expected one of: " + ", ".join(DEFAULT_FILENAMES)
    )


def _split_target_arguments(
    target_name: str, tokens: T.List[str], parameters: T.List[str], filename: str
) -> T.Dict[str, str]:
    """Turn CLI tokens into named arguments.

    An argument for the first declared parameter may be given positionally, but it
    must come first and may not repeat a named one.
    """
    arguments: T.Dict[str, str] = {}
    positional: T.Optional[str] = None

    for index, token in enumerate(tokens):
        name, separator, value = token.partition("=")
        if separator and name:
            if name == positional:
                raise ArgumentError(
                    f"'{name}' was given both positionally and by name",
                    filename=filename,
                )
            arguments[name] = value
            continue

        # A positional token: only the very first one, naming the first parameter.
        if index != 0:
            raise ArgumentError(
                "a positional argument must come first", filename=filename
            )
        if not parameters:
            raise ArgumentError(
                f"{target_name}() takes no parameters", filename=filename
            )
        positional = parameters[0]
        arguments[positional] = token

    return arguments


def _print_targets(module) -> None:
    from jazzoo.functions.rules.get_targets import get_targets

    for function in get_targets(module):
        print(function.name)


def _run(args) -> int:
    from jazzoo.expressions.actions.evaluate_expression import evaluate_expression
    from jazzoo.functions.actions.call_function import call_function
    from jazzoo.functions.rules.get_target_by_path import get_target_by_path
    from jazzoo.modules.actions.parse_module import _GLOBALS, parse_module
    from jazzoo.modules.models.frame import Frame

    filename = args.file or _find_default_file()
    module = parse_module(filename)

    tokens = list(args.rest)
    if args.list_targets or not tokens:
        _print_targets(module)
        return 0

    target_name, tokens = tokens[0], tokens[1:]
    target = get_target_by_path(module, target_name)
    if target is None:
        raise JazzooError(
            f"no such target: {target_name}", filename=module.filename
        )

    arguments = _split_target_arguments(
        target_name,
        tokens,
        [p.name for p in target.parameters],
        module.filename,
    )

    frame = Frame(module=module, root_module=module, globals_=_GLOBALS)
    call_function(target, arguments, frame, evaluate_expression)
    return 0


def main(argv: T.Optional[T.List[str]] = None) -> int:
    args = _parse_args(argv)
    if args.help:
        print("usage: jaz [--list] [--file <path>] [--trace] <target> [arg=value ...]")
        return 0

    try:
        return _run(args)
    except JazzooError as error:
        location = error.filename or ""
        if location and error.line is not None:
            location = f"{os.path.basename(location)}:{error.line}"
        elif location:
            location = os.path.basename(location)
        prefix = f"{location}: " if location else ""
        print(f"{prefix}error: {error.message}", file=sys.stderr)
        if args.trace:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
