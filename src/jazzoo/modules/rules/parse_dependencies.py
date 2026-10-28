import re
import typing as T

from jazzoo.functions.models.call_site import CallSite
from jazzoo.modules.rules.parse_call_arguments import parse_call_arguments


def parse_dependencies(text: str, filename: str, line: int) -> T.List[CallSite]:
    """Parse the dependency list that follows a function's colon."""
    dependencies: T.List[CallSite] = []
    for match in re.finditer(r"([A-Za-z_][A-Za-z0-9_.-]*)\s*\(([^)]*)\)", text):
        dependencies.append(
            CallSite(
                target_path=match.group(1),
                arguments=parse_call_arguments(match.group(2), filename, line),
                filename=filename,
                line=line,
            )
        )
    return dependencies
