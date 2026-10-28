import typing as T

from jazzoo.functions.models.function import Function
from jazzoo.modules.models.assignment import Assignment
from jazzoo.modules.models.builtin_call import BuiltinCall
from jazzoo.utils.dataclass import dataclass


@dataclass
class ParsedSource:
    assignments: T.List[Assignment] = []
    functions: T.List[Function] = []
    imports: T.List[T.Any] = []
    # Assignments and ⚙️ calls in file order, which is the order they run in.
    statements: T.List[T.Union[Assignment, BuiltinCall]] = []
