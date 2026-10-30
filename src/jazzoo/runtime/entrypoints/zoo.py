import argparse
import os
import sys
import traceback
import typing as T

from jazzoo.errors import JazzooError
from jazzoo.runtime.entrypoints.jazzoo import _parse_args as _parse_jaz_args
from jazzoo.runtime.utils.format_error import format_error
from jazzoo.settings import get_active_zoo_env
from jazzoo.zoo.actions.activate_zoo_env import activate_zoo_env
from jazzoo.zoo.actions.forget_zoo_env import forget_zoo_env
from jazzoo.zoo.actions.init_zoo_env import init_zoo_env
from jazzoo.zoo.actions.install_fish_files import install_fish_files
from jazzoo.zoo.actions.run_in_zoo_env import run_in_zoo_env
from jazzoo.zoo.errors import ZooError, ZooUsageError
from jazzoo.zoo.rules.format_zoo_env_line import format_zoo_env_line
from jazzoo.zoo.rules.format_zoo_env_list import format_zoo_env_list
from jazzoo.zoo.rules.get_recent_zoo_env import get_recent_zoo_env
from jazzoo.zoo.rules.get_zoo_env import get_zoo_env
from jazzoo.zoo.rules.list_zoo_envs import list_zoo_envs


def _parse_env_args(argv: T.List[str]):
    parser = argparse.ArgumentParser(
        prog="zoo env", description="Register and activate zoo environments."
    )
    parser.add_argument("name", nargs="?")
    parser.add_argument("--latest", action="store_true")
    parser.add_argument("--init", action="store_true")
    parser.add_argument("--forget", action="store_true")
    parser.add_argument("--list", dest="list_envs", action="store_true")
    parser.add_argument("--names", action="store_true")
    parser.add_argument("--install-fish", action="store_true")
    venv_group = parser.add_mutually_exclusive_group()
    venv_group.add_argument("--create-venv", action="store_true")
    venv_group.add_argument("--use-venv")
    parser.add_argument("--without-pip", action="store_true")
    args = parser.parse_args(argv)

    # The rules of how the options combine (design section 3.1)
    if args.init + args.forget + args.list_envs + args.install_fish > 1:
        parser.error("--init, --forget, --list and --install-fish exclude one another")
    if args.install_fish and (args.name or args.latest):
        parser.error("--install-fish takes no environment")
    if args.names and not args.list_envs:
        parser.error("--names is only valid with --list")
    if args.latest and args.name:
        parser.error("<name>, - and --latest exclude one another")
    if args.list_envs and (args.name or args.latest):
        parser.error("--list takes no environment")
    if (args.init or args.forget) and (args.latest or args.name == "-"):
        parser.error("--init and --forget take a name, not - or --latest")
    if args.forget and not args.name:
        parser.error("--forget needs a name")
    if args.init and not (args.create_venv or args.use_venv):
        parser.error("--init needs --create-venv or --use-venv")
    if (args.create_venv or args.use_venv) and not args.init:
        parser.error("--create-venv and --use-venv are only valid with --init")
    if args.without_pip and not args.create_venv:
        parser.error("--without-pip is only valid with --create-venv")
    if not (
        args.init
        or args.forget
        or args.list_envs
        or args.install_fish
        or args.name
        or args.latest
    ):
        parser.error("no environment was given")
    return args


def _run_env(argv: T.List[str]) -> int:
    args = _parse_env_args(argv)

    if args.list_envs:
        if args.names:
            lines = [env.name for env in list_zoo_envs()]
        else:
            lines = format_zoo_env_list(list_zoo_envs(), get_active_zoo_env())
        for line in lines:
            print(line)
        return 0

    if args.install_fish:
        # The messages go to stderr: the stdout of zoo env is for lines to source
        for path in install_fish_files():
            print(f"Wrote {path}", file=sys.stderr)
        print("Open a new fish shell to use zz.", file=sys.stderr)
        return 0

    if args.forget:
        env = forget_zoo_env(args.name)
        print(
            f'Forgot zoo environment "{env.name}". '
            f"Its venv was not removed: {env.venv_dir}",
            file=sys.stderr,
        )
        return 0

    if args.init:
        root_dir = os.getcwd()
        name = args.name or os.path.basename(root_dir)
        venv_dir = (
            os.path.join(root_dir, ".venv")
            if args.create_venv
            else os.path.abspath(args.use_venv)
        )
        init_zoo_env(
            name,
            root_dir,
            venv_dir,
            create=args.create_venv,
            with_pip=not args.without_pip,
        )
    elif args.latest:
        name = get_recent_zoo_env("latest")
    elif args.name == "-":
        name = get_recent_zoo_env("previous")
    else:
        name = args.name

    print(activate_zoo_env(name))
    return 0


def _complete(argv: T.List[str]) -> int:
    from jazzoo.completions.utils.print_completions import print_completions
    from jazzoo.zoo.rules.get_zoo_completions import get_zoo_completions

    return print_completions(argv, get_zoo_completions)


def _refuse_file_option(argv: T.List[str]):
    # After --, a word is a target name
    for word in argv[: argv.index("--")] if "--" in argv else argv:
        if word == "--file" or word.startswith("--file="):
            raise ZooUsageError(
                "--file is not valid with zoo; import the file as a layer instead"
            )


def _print_active_env(args) -> int:
    """`zoo --which` without a path: print the env that the shell activated, if any.

    It only reads the registry, so unlike a target it needs no venv of an env.
    """
    for option, is_set in (
        ("--list", args.list_targets),
        ("--list-all", args.list_all),
    ):
        if is_set:
            raise JazzooError(f"--which cannot be combined with {option}")

    name = get_active_zoo_env()
    if name:
        print(format_zoo_env_line(get_zoo_env(name)))
    return 0


def run(argv: T.Optional[T.List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["env"]:
        return _run_env(argv[1:])
    if argv[:1] == ["--complete"]:
        return _complete(argv[1:])

    # Everything else is a jaz call, also `zoo -- env`
    _refuse_file_option(argv)
    args = _parse_jaz_args(argv)
    if args.which and not args.rest and not args.help:
        return _print_active_env(args)
    return run_in_zoo_env(argv)


def main(argv: T.Optional[T.List[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        return run(argv)
    except ZooError as error:
        print(f"zoo: error: {error.message}", file=sys.stderr)
        return 1
    except JazzooError as error:
        # An error of the jaz run, printed as jaz prints it
        print(format_error(error), file=sys.stderr)
        if "--trace" in argv:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
