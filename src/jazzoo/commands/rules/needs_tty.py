import sys


def needs_tty(capture: bool) -> bool:
    # A tty would mix stderr into captured output, and docker refuses one when the
    # script has no terminal
    if capture:
        return False
    return sys.stdin.isatty() and sys.stdout.isatty()
