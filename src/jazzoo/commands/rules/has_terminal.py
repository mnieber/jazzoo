from ..settings import TERMINAL


def has_terminal() -> bool:
    try:
        with open(TERMINAL, "w"):
            return True
    except OSError:
        return False
