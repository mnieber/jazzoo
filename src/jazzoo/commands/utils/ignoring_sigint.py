import contextlib
import signal
import threading
import typing as T


@contextlib.contextmanager
def ignoring_sigint() -> T.Iterator[None]:
    # Signal handlers can only be changed in the main thread
    if threading.current_thread() is not threading.main_thread():
        yield
        return

    old_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        yield
    finally:
        signal.signal(signal.SIGINT, old_handler)
