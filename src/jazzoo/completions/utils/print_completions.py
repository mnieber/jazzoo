import sys
import typing as T

from jazzoo.completions.models.candidate import Candidate


def print_completions(
    argv: T.List[str], get_candidates: T.Callable[[T.List[str]], T.List[Candidate]]
) -> int:
    if argv[:1] != ["--"]:
        print("usage: --complete -- <word> ...", file=sys.stderr)
        raise SystemExit(2)

    # Fish shows the output in the command line, so a completion never fails
    try:
        candidates = get_candidates(argv[1:])
    except Exception:
        return 0
    for candidate in candidates:
        if candidate.description is None:
            print(candidate.text)
        else:
            print(f"{candidate.text}\t{candidate.description}")
    return 0
