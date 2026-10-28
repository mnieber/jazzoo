import typing as T

from jazzoo.utils.dataclass import dataclass


@dataclass
class And:
    # `left and right`. Yields `left` when it is falsy, otherwise `right`, and does
    # not evaluate `right` at all in the first case.
    left: T.Any
    right: T.Any


@dataclass
class Or:
    # `left or right`. Yields `left` when it is truthy, otherwise `right`, and does
    # not evaluate `right` at all in the first case.
    left: T.Any
    right: T.Any


@dataclass
class Not:
    # `not operand`. Always yields a real boolean.
    operand: T.Any
