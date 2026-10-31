import typing as T

from jazzoo.functions.models.function import Function
from jazzoo.module_validation.rules.validate_function import validate_function
from jazzoo.modules.models.module import Module


def validate_module(
    module: Module, function_valued: T.Optional[T.Dict[str, Function]] = None
) -> None:
    """Check every call site in the module against the function it names.

    Raised at load time, before any subprocess runs, so a mistake in one target
    surfaces even when a different target is invoked.

    `function_valued` maps module-level variables that hold a function to the
    function they hold, so a call through a curried name resolves.
    """
    for function in module.functions:
        if function.module is not None and function.module is not module:
            # An imported or exported function resolves its calls in the module
            # that defines it, and was validated when that module was loaded.
            continue
        validate_function(function, module, function_valued or {})
