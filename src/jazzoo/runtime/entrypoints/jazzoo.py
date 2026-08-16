import argparse
import sys
import typing as T


def _parse_args(argv: T.Optional[T.List[str]] = None):
    parser = argparse.ArgumentParser(
        prog="jaz", description="Run targets from a .jaz file."
    )
    parser.add_argument("--file", dest="file", default=None)
    parser.add_argument("--list", dest="list_targets", action="store_true")
    parser.add_argument("--trace", dest="trace", action="store_true")
    parser.add_argument("rest", nargs=argparse.REMAINDER)
    return parser.parse_args(argv)


def main(argv: T.Optional[T.List[str]] = None) -> int:
    raise NotImplementedError


if __name__ == "__main__":
    sys.exit(main())
