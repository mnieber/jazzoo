from jazzoo.references.rules.match_sigil import SIGILS


def contains_sigil(text: str) -> bool:
    return any(sigil in text for sigil in SIGILS)
