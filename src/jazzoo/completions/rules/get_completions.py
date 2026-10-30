import typing as T

from jazzoo.completions.models.candidate import Candidate
from jazzoo.completions.rules.complete_arguments import complete_arguments
from jazzoo.completions.rules.complete_file_names import complete_file_names
from jazzoo.completions.rules.complete_options import complete_options
from jazzoo.completions.rules.complete_target import complete_target
from jazzoo.modules.models.module import Module

FILE_OPTION = "--file"


def get_completions(
    words: T.List[str],
    options: T.Sequence[str],
    load_module: T.Callable[[T.Optional[str]], T.Optional[Module]],
) -> T.List[Candidate]:
    *done, word = words or [""]

    # Split the finished words into the --file and the target with its arguments
    filename: T.Optional[str] = None
    positional: T.List[str] = []
    expects_file = False
    after_dashes = False
    for done_word in done:
        if expects_file:
            filename, expects_file = done_word, False
        elif after_dashes or not done_word.startswith("-"):
            positional.append(done_word)
        elif done_word == "--":
            after_dashes = True
        elif FILE_OPTION in options and done_word == FILE_OPTION:
            expects_file = True
        elif FILE_OPTION in options and done_word.startswith(FILE_OPTION + "="):
            filename = done_word.partition("=")[2]
        # Other options, also unknown ones, are skipped

    if expects_file:
        return complete_file_names(word)
    if word.startswith("-") and not after_dashes:
        return complete_options(options, word)

    module = load_module(filename)
    if module is None:
        return []
    if not positional:
        return complete_target(module, word)
    if "=" in word:
        name, _, value = word.partition("=")
        return complete_file_names(value, prefix=name + "=")
    return complete_arguments(module, positional[0], positional[1:], word)
