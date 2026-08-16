import typing as T


class JazzooError(Exception):
    def __init__(
        self,
        message: str,
        filename: T.Optional[str] = None,
        line: T.Optional[int] = None,
    ):
        super().__init__(message)
        self.message = message
        self.filename = filename
        self.line = line

    def __str__(self) -> str:
        if self.filename is None:
            return self.message
        location = self.filename
        if self.line is not None:
            location = f"{location}:{self.line}"
        return f"{location}: {self.message}"


class ParseError(JazzooError):
    pass


class ResolutionError(JazzooError):
    pass


class ArgumentError(JazzooError):
    pass


# Named ModuleImportError rather than ImportError so it does not shadow the builtin.
class ModuleImportError(JazzooError):
    pass


class ExecutionError(JazzooError):
    pass
