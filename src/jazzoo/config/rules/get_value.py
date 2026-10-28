import typing as T

from ..errors import ConfigExpansionError
from ..models.loaded_config import LoadedConfig
from ..utils.format_config_path import format_config_path
from ..utils.render_scalar import render_scalar

Path = T.Tuple[T.Any, ...]

_MISSING = object()


class MissingPathError(Exception):
    def __init__(self, segment: T.Any):
        super().__init__(segment)
        self.segment = segment


def get_value(loaded: LoadedConfig, segments: T.Sequence[T.Any]) -> T.Any:
    return _get(loaded, segments, stack=[])


def _get(loaded: LoadedConfig, segments: T.Sequence[T.Any], stack: T.List[Path]):
    node: T.Any = loaded.tree
    path: T.List[T.Any] = []
    # Once a string is expanded, the values below it are expanded already
    is_raw = True

    for segment in segments:
        key = _find_key(node, segment)
        if key is _MISSING:
            raise MissingPathError(segment)
        path.append(key)
        node = node[key]
        if is_raw and isinstance(node, str):
            node = _expand_string_at(loaded, node, tuple(path), stack)
            is_raw = False

    return _expand_tree(loaded, node, tuple(path), stack) if is_raw else node


def _find_key(node: T.Any, segment: T.Any) -> T.Any:
    if isinstance(node, dict):
        if segment in node:
            return segment
        # YAML keys are not always strings, e.g. `8080: web`
        for key in node:
            if str(key) == str(segment):
                return key
        return _MISSING
    if isinstance(node, list):
        text = str(segment)
        if text.isdigit() and int(text) < len(node):
            return int(text)
        return _MISSING
    return _MISSING


def _expand_tree(loaded: LoadedConfig, node: T.Any, path: Path, stack: T.List[Path]):
    if isinstance(node, dict):
        return {
            key: _expand_tree(loaded, value, path + (key,), stack)
            for key, value in node.items()
        }
    if isinstance(node, list):
        return [
            _expand_tree(loaded, value, path + (index,), stack)
            for index, value in enumerate(node)
        ]
    if isinstance(node, str):
        return _expand_string_at(loaded, node, path, stack)
    return node


def _expand_string_at(
    loaded: LoadedConfig, text: str, path: Path, stack: T.List[Path]
) -> T.Any:
    if path in loaded.expanded:
        return loaded.expanded[path]

    if path in stack:
        cycle = stack[stack.index(path) :] + [path]
        raise ConfigExpansionError(
            f"{_context(loaded, path)}: reference cycle: "
            + " -> ".join(format_config_path(p) for p in cycle)
        )

    stack.append(path)
    try:
        value = _expand_string(loaded, text, path, stack)
    finally:
        stack.pop()

    loaded.expanded[path] = value
    return value


def _expand_string(
    loaded: LoadedConfig, text: str, path: Path, stack: T.List[Path]
) -> T.Any:
    parts = _parse(loaded, text, path)

    # A string that is one reference yields the referenced value with its own type
    if len(parts) == 1 and isinstance(parts[0], _Expression):
        return _evaluate(loaded, parts[0].content, path, stack)

    result = []
    for part in parts:
        if isinstance(part, _Expression):
            value = _evaluate(loaded, part.content, path, stack)
            if isinstance(value, (dict, list)):
                raise ConfigExpansionError(
                    f"{_context(loaded, path)}: cannot render a "
                    f"{type(value).__name__} inside a string: ${{{part.content}}}"
                )
            result.append(render_scalar(value))
        else:
            result.append(part)
    return "".join(result)


def _evaluate(
    loaded: LoadedConfig, content: str, path: Path, stack: T.List[Path]
) -> T.Any:
    # Nested expressions are expanded first
    expression = _expand_nested(loaded, content, path, stack)

    if expression.startswith("/"):
        segments = [segment for segment in expression.split("/") if segment]
        try:
            return _get(loaded, segments, stack)
        except MissingPathError:
            raise ConfigExpansionError(
                f"{_context(loaded, path)}: reference to a missing path: {expression}"
            )

    name, has_default, default = expression.partition(":-")
    value = loaded.environ.get(name)
    if has_default and not value:
        return default
    if value is None:
        raise ConfigExpansionError(
            f"{_context(loaded, path)}: environment variable is not set: {name}"
        )
    return value


def _expand_nested(
    loaded: LoadedConfig, content: str, path: Path, stack: T.List[Path]
) -> str:
    result = []
    for part in _parse(loaded, content, path):
        if isinstance(part, _Expression):
            value = _evaluate(loaded, part.content, path, stack)
            if isinstance(value, bool) or not isinstance(value, (str, int, float)):
                raise ConfigExpansionError(
                    f"{_context(loaded, path)}: a nested reference must yield a "
                    f"string or number: ${{{part.content}}}"
                )
            result.append(render_scalar(value))
        else:
            result.append(part)
    return "".join(result)


class _Expression:
    def __init__(self, content: str):
        self.content = content


def _parse(
    loaded: LoadedConfig, text: str, path: Path
) -> T.List[T.Union[str, _Expression]]:
    parts: T.List[T.Union[str, _Expression]] = []
    literal: T.List[str] = []
    index = 0

    while index < len(text):
        if text.startswith("$${", index):
            literal.append("${")
            index += 3
        elif text.startswith("${", index):
            end = _find_closing_brace(text, index + 2)
            if end is None:
                raise ConfigExpansionError(
                    f"{_context(loaded, path)}: unclosed '${{' in: {text}"
                )
            if literal:
                parts.append("".join(literal))
                literal = []
            parts.append(_Expression(text[index + 2 : end]))
            index = end + 1
        else:
            literal.append(text[index])
            index += 1

    if literal:
        parts.append("".join(literal))
    return parts


def _find_closing_brace(text: str, start: int) -> T.Optional[int]:
    depth = 1
    index = start
    while index < len(text):
        if text.startswith("$${", index):
            index += 3
        elif text.startswith("${", index):
            depth += 1
            index += 2
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return index
            index += 1
        else:
            index += 1
    return None


def _context(loaded: LoadedConfig, path: Path) -> str:
    # The value comes from the last file that has it
    for config_file, file_tree in reversed(loaded.file_trees):
        if _has_path(file_tree, path):
            return f"{config_file}: {format_config_path(path)}"
    return format_config_path(path)


def _has_path(tree: T.Any, path: Path) -> bool:
    node = tree
    for key in path:
        if isinstance(node, dict) and key in node:
            node = node[key]
        elif isinstance(node, list) and isinstance(key, int) and key < len(node):
            node = node[key]
        else:
            return False
    return True
