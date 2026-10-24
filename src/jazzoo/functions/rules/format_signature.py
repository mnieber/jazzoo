from jazzoo.functions.models.function import Function


def format_signature(function: Function, path: str) -> str:
    """Render a target as `path(param, param="default")`.

    This is what `jaz --list <target>` prints, so a caller can see which arguments
    the target takes and which of them have defaults.
    """
    parts = []
    for parameter in function.parameters:
        if parameter.default is None:
            parts.append(parameter.name)
        else:
            # The default as written, so a string keeps its quotes and a variable
            # reference shows by name.
            parts.append(f"{parameter.name}={parameter.default}")
    return f"{path}({', '.join(parts)})"
