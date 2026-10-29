import argparse
import sys
import typing as T

from ..actions.run import run as run_command
from ..errors import (
    CommandAbortedError,
    CommandError,
    CommandNotFoundError,
    UsageError,
)

USAGE = (
    "usage: jaz-run [--echo] [--] <executable> [<argument> ...]\n"
    '       jaz-run [--echo] -c "<command>"'
)


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str):
        raise UsageError(message)


def _parse_args(argv: T.Optional[T.List[str]] = None):
    parser = _ArgumentParser(prog="jaz-run", add_help=False)
    parser.add_argument("--echo", dest="echo", action="store_true")
    parser.add_argument("-c", dest="string_command", default=None)
    parser.add_argument("--help", "-h", dest="help", action="store_true")
    # The first argument that is not an option of jaz-run starts the command
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser.parse_args(argv)


def _get_command(args) -> T.Union[str, T.List[str]]:
    command = list(args.command)
    if command[:1] == ["--"]:
        command = command[1:]

    if args.string_command is not None:
        if command:
            raise UsageError("-c takes a single command")
        return args.string_command

    if not command:
        raise UsageError("no command given")
    return command


def run(argv: T.Optional[T.List[str]] = None) -> int:
    args = _parse_args(argv)
    if args.help:
        print(USAGE)
        return 0

    result = run_command(_get_command(args), check=False, echo=args.echo)
    return result.returncode


def main(argv: T.Optional[T.List[str]] = None) -> int:
    try:
        return run(argv)
    except KeyboardInterrupt:
        return 130
    except CommandAbortedError as error:
        print(f"jaz-run: {error}", file=sys.stderr)
        return 130
    except CommandNotFoundError as error:
        print(f"jaz-run: {error}", file=sys.stderr)
        return 127
    except (CommandError, ValueError) as error:
        print(f"jaz-run: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
