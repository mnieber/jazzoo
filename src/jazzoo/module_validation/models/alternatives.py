import typing as T

from jazzoo.functions.models.function import Function


class Alternatives:
    """A name that holds one of several functions, chosen at run time.

    It resolves - the name is callable - but its arguments can only be checked
    against the set, since which member is called is not decidable here.
    """

    def __init__(self, functions: T.List[Function], not_functions: T.List[str]):
        self.functions = functions
        # Operands that name no function. Harmless until the value is called.
        self.not_functions = not_functions
        # Enough of the CurriedFunction shape for the call path to treat it alike.
        self.function = functions[0]
        self.bound: T.Dict[str, str] = {}
        self.explicitly_unbound: T.List[str] = []
