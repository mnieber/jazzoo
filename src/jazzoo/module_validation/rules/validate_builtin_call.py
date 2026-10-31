import typing as T

from jazzoo.errors import ResolutionError
from jazzoo.module_validation.rules.validate_arguments import validate_arguments


def validate_builtin_call(
    name: str,
    arguments: T.List[T.Tuple[T.Optional[str], str]],
    filename: T.Optional[str],
    line: T.Optional[int],
) -> None:
    """Check a call to a ⚙️ function against its parameters."""
    from jazzoo.functions.actions.call_builtin_function import BUILTIN_PARAMETERS

    parameters = BUILTIN_PARAMETERS.get(name)
    if parameters is None:
        raise ResolutionError(
            f"no such function: ⚙️.{name}", filename=filename, line=line
        )
    validate_arguments(f"⚙️.{name}", f"⚙️.{name}", parameters, arguments, filename, line)
