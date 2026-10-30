from jazzoo.utils.dataclass import dataclass


@dataclass
class FunctionHeader:
    name: str
    # The text between the parentheses
    params: str
    # The text after the colon
    rest: str
