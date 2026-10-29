import typing as T

if T.TYPE_CHECKING:
    from .models.command_result import CommandResult


class CommandError(Exception):
    pass


class CommandNotFoundError(CommandError):
    pass


class CommandFailedError(CommandError):
    def __init__(self, message: str, result: "CommandResult"):
        super().__init__(message)
        self.result = result
