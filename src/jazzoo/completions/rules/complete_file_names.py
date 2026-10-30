import os
import typing as T

from jazzoo.completions.models.candidate import Candidate


def complete_file_names(word: str, prefix: str = "") -> T.List[Candidate]:
    dirname, basename = os.path.split(word)
    try:
        names = sorted(os.listdir(dirname or "."))
    except OSError:
        return []

    candidates = []
    for name in names:
        # Dotfiles are hidden, unless the developer types the dot
        if name.startswith(".") and not basename.startswith("."):
            continue
        if not name.startswith(basename):
            continue
        path = os.path.join(dirname, name)
        if os.path.isdir(path):
            path += "/"
        candidates.append(Candidate(prefix + path))
    return candidates
