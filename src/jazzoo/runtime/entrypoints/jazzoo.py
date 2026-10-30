import argparse
import os
import sys
import traceback
import typing as T

from jazzoo.commands.rules.has_terminal import has_terminal
from jazzoo.commands.settings import CONFIRM_ENV_VAR
from jazzoo.errors import ArgumentError, JazzooError
from jazzoo.runtime.utils.format_error import format_error
from jazzoo.settings import DEFAULT_FILENAMES

# The options of jaz that --complete offers
OPTIONS = (
    "--list",
    "--list-all",
    "--which",
    "--file",
    "--trace",
    "--confirm",
    "--help",
)


def _parse_args(argv: T.Optional[T.List[str]] = None):
    parser = argparse.ArgumentParser(
        prog="jaz", description="Run targets from a .jaz file.", add_help=False
    )
    parser.add_argument("--file", dest="file", default=None)
    parser.add_argument("--list", dest="list_targets", action="store_true")
    parser.add_argument("--list-all", dest="list_all", action="store_true")
    parser.add_argument("--which", dest="which", action="store_true")
    parser.add_argument("--trace", dest="trace", action="store_true")
    parser.add_argument("--confirm", dest="confirm", action="store_true")
    parser.add_argument("--help", "-h", dest="help", action="store_true")
    parser.add_argument("rest", nargs="*")
    # The options may also follow the target and its arguments
    return parser.parse_intermixed_args(argv)


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


def _print_listing(module, path: T.Optional[str]) -> int:
    """Print what `--list` should show, optionally scoped to a dotted path.

    With no path, the root module's own targets and layers. With one, whatever is at
    that path: a layer's members, or a target's signature.
    """
    from jazzoo.functions.rules.format_signature import format_signature
    from jazzoo.functions.rules.get_target_by_path import (
        get_layer_by_path,
        get_target_by_path,
    )
    from jazzoo.modules.rules.list_targets import list_one_level

    if path is None:
        for line in list_one_level(module):
            print(line)
        return 0

    layer = get_layer_by_path(module, path)
    if layer is not None:
        for line in list_one_level(layer, prefix=path + "."):
            print(line)
        return 0

    target = get_target_by_path(module, path)
    if target is not None:
        print(format_signature(target, path))
        return 0

    raise JazzooError(f"no such target: {path}", filename=module.filename)


def _switch_on_confirm():
    if not has_terminal():
        raise JazzooError("--confirm needs a terminal")
    os.environ[CONFIRM_ENV_VAR] = "1"


def _expand_alias(alias: str, args, filename: str) -> T.Tuple[str, T.List[str]]:
    from jazzoo.aliases.rules.expand_alias import expand_alias

    expansion = expand_alias(alias)
    if expansion is None:
        raise JazzooError(f"no such target: {alias}", filename=filename)

    # The options of the expansion are added to those of the command line
    alias_args = _parse_args(expansion)
    if alias_args.confirm and not args.confirm:
        args.confirm = True
        _switch_on_confirm()
    args.trace = args.trace or alias_args.trace

    return alias_args.rest[0], alias_args.rest[1:]


def _print_which(args, invocation_dir: T.Optional[str]) -> int:
    """Print the file that defines the target (or layer) that args.rest names.

    Nothing runs, so the module is loaded without running its statements.
    """
    from jazzoo.functions.rules.get_definition_file import get_definition_file
    from jazzoo.modules.actions.parse_module import parse_module

    for option, is_set in (
        ("--list", args.list_targets),
        ("--list-all", args.list_all),
    ):
        if is_set:
            raise JazzooError(f"--which cannot be combined with {option}")
    if not args.rest:
        raise JazzooError("--which needs a target")
    if len(args.rest) > 1:
        raise JazzooError("--which takes no arguments")

    filename = args.file or _find_default_file()
    module = parse_module(filename, invocation_dir=invocation_dir, run_statements=False)

    path = args.rest[0]
    definition_file = get_definition_file(module, path)
    if definition_file is None:
        from jazzoo.aliases.rules.expand_alias import expand_alias

        # The options of the expansion change how a target runs, so they are skipped
        expansion = expand_alias(path)
        if expansion is None:
            raise JazzooError(f"no such target: {path}", filename=module.filename)
        alias, path = path, _parse_args(expansion).rest[0]
        definition_file = get_definition_file(module, path)
        if definition_file is None:
            raise JazzooError(
                f'no such target: {path} (the expansion of alias "{alias}")',
                filename=module.filename,
            )

    print(definition_file)
    return 0


def _run(args, invocation_dir: T.Optional[str]) -> int:
    from jazzoo.expressions.actions.evaluate_expression import evaluate_expression
    from jazzoo.functions.actions.call_function import call_function
    from jazzoo.functions.rules.get_target_by_path import get_target_by_path
    from jazzoo.modules.actions.parse_module import _GLOBALS, parse_module
    from jazzoo.modules.models.frame import Frame

    # Only the commands of a target are confirmed, so listing needs no terminal
    runs_target = bool(args.rest) and not args.list_targets and not args.list_all
    if args.confirm and runs_target:
        _switch_on_confirm()

    filename = args.file or _find_default_file()
    module = parse_module(filename, invocation_dir=invocation_dir)

    tokens = list(args.rest)

    if args.list_all:
        from jazzoo.modules.rules.list_targets import list_all

        for line in list_all(module):
            print(line)
        return 0

    if args.list_targets or not tokens:
        return _print_listing(module, tokens[0] if tokens else None)

    target_name, tokens = tokens[0], tokens[1:]
    target = get_target_by_path(module, target_name)
    alias_tokens: T.List[str] = []
    if target is None:
        alias = target_name
        target_name, alias_tokens = _expand_alias(alias, args, module.filename)
        target = get_target_by_path(module, target_name)
        if target is None:
            raise JazzooError(
                f'no such target: {target_name} (the expansion of alias "{alias}")',
                filename=module.filename,
            )

    # The arguments of the alias are presets that the command line overrides
    parameters = [p.name for p in target.parameters]
    arguments = {
        **_split_target_arguments(
            target_name, alias_tokens, parameters, module.filename
        ),
        **_split_target_arguments(target_name, tokens, parameters, module.filename),
    }

    frame = Frame(module=module, root_module=module, globals_=_GLOBALS)
    call_function(target, arguments, frame, evaluate_expression)
    return 0


def _complete(argv: T.List[str]) -> int:
    from jazzoo.completions.rules.get_completions import get_completions
    from jazzoo.completions.rules.load_module_for_completion import (
        load_module_for_completion,
    )
    from jazzoo.completions.utils.print_completions import print_completions

    def load_module(filename: T.Optional[str]):
        return load_module_for_completion(filename, ".")

    return print_completions(
        argv, lambda words: get_completions(words, OPTIONS, load_module)
    )


def _run_or_help(args, invocation_dir: T.Optional[str]) -> int:
    if args.help:
        print(
            "usage: jaz [--list [<path>]] [--list-all] [--which <path>] "
            "[--file <path>] [--trace] [--confirm] <target> [arg=value ...]"
        )
        return 0
    if args.which:
        return _print_which(args, invocation_dir)
    return _run(args, invocation_dir)


def run(
    argv: T.Optional[T.List[str]] = None, invocation_dir: T.Optional[str] = None
) -> int:
    # Lets the errors pass. invocation_dir defaults to the current directory.
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--complete"]:
        return _complete(argv[1:])
    return _run_or_help(_parse_args(argv), invocation_dir)


def main(argv: T.Optional[T.List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--complete"]:
        return _complete(argv[1:])
    args = _parse_args(argv)
    try:
        return _run_or_help(args, None)
    except JazzooError as error:
        print(format_error(error), file=sys.stderr)
        if args.trace:
            traceback.print_exc()
        return 1
    except KeyboardInterrupt:
        if args.trace:
            traceback.print_exc()
        return 130


if __name__ == "__main__":
    sys.exit(main())
