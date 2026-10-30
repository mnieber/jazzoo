import typing as T

from jazzoo.completions.models.candidate import Candidate


def complete_options(options: T.Sequence[str], word: str) -> T.List[Candidate]:
    return [Candidate(option) for option in options if option.startswith(word)]
