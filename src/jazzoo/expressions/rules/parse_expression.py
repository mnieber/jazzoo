import json
import typing as T

from jazzoo.errors import ParseError
from jazzoo.expressions.models.boolean import And, Not, Or
from jazzoo.expressions.models.literal import Literal
from jazzoo.expressions.models.path_join import PathJoin
from jazzoo.expressions.models.pipe import Pipe
from jazzoo.expressions.models.ternary import Comparison, Ternary
from jazzoo.expressions.rules.tokenize_expression import Token, tokenize_expression
from jazzoo.utils.dataclass import dataclass


@dataclass
class Call:
    # The whole `🐭.name(args)` text; arguments are parsed when it is evaluated.
    text: str


@dataclass
class JsonLiteral:
    # A JSON scalar, array or object written literally in the source.
    value: T.Any


@dataclass
class CallValue:
    # `(expr)(args)`: the callee is computed, so it cannot be looked up by path the
    # way a plain `🐭.f(args)` call is. The argument text is parsed at eval time,
    # exactly as for Call.
    target: T.Any
    args: str


@dataclass
class Curry:
    target: T.Any
    text: str


@dataclass
class ReferenceText:
    # A reference in expression position; parsed into a Reference at eval time so
    # the marker rules stay in one place.
    text: str


class _Parser:
    def __init__(self, tokens: T.List[Token], source: str):
        self.tokens = tokens
        self.source = source
        self.pos = 0

    def peek(self) -> T.Optional[Token]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def take(self) -> Token:
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def parse(self) -> T.Any:
        node = self.parse_ternary()
        if self.peek() is not None:
            raise ParseError(
                f"unexpected {self.peek().text!r} in expression: {self.source!r}"
            )
        return node

    def parse_ternary(self) -> T.Any:
        value = self.parse_or()
        token = self.peek()
        if token is None or token.kind != "if":
            return value
        self.take()
        condition = self.parse_condition()
        token = self.peek()
        if token is None or token.kind != "else":
            raise ParseError(f"ternary without an else: {self.source!r}")
        self.take()
        # Right-associative: the else branch may be another ternary.
        return Ternary(value=value, condition=condition, otherwise=self.parse_ternary())

    def parse_condition(self) -> T.Any:
        return self.parse_or()

    def parse_or(self) -> T.Any:
        left = self.parse_and()
        while self.peek() is not None and self.peek().kind == "or":
            self.take()
            left = Or(left=left, right=self.parse_and())
        return left

    def parse_and(self) -> T.Any:
        left = self.parse_not()
        while self.peek() is not None and self.peek().kind == "and":
            self.take()
            left = And(left=left, right=self.parse_not())
        return left

    def parse_not(self) -> T.Any:
        if self.peek() is not None and self.peek().kind == "not":
            self.take()
            return Not(operand=self.parse_not())
        return self.parse_comparison()

    def parse_comparison(self) -> T.Any:
        left = self.parse_pipe()
        token = self.peek()
        if token is not None and token.kind == "==":
            self.take()
            return Comparison(left=left, right=self.parse_pipe())
        return left

    def parse_pipe(self) -> T.Any:
        # `|` binds looser than `/`, so `a / b | f` pipes the whole join.
        value = self.parse_path()
        stages: T.List[T.Any] = []
        while self.peek() is not None and self.peek().kind == "|":
            self.take()
            stages.append(self.parse_path())
        if not stages:
            return value
        return Pipe(value=value, stages=stages)

    def parse_path(self) -> T.Any:
        left = self.parse_primary()
        while self.peek() is not None and self.peek().kind == "/":
            self.take()
            left = PathJoin(left=left, right=self.parse_primary())
        return left

    def parse_primary(self) -> T.Any:
        token = self.peek()
        if token is None:
            raise ParseError(f"unexpected end of expression: {self.source!r}")

        if token.kind == "(":
            # A group re-enters at the very top of the grammar, so parentheses can
            # override every precedence - a ternary included.
            self.take()
            inner = self.parse_ternary()
            closing = self.peek()
            if closing is None or closing.kind != ")":
                raise ParseError(
                    f"unbalanced parentheses in expression: {self.source!r}"
                )
            self.take()
            while self.peek() is not None and self.peek().kind == "call-args":
                inner = CallValue(target=inner, args=self.take().text)
            return inner

        if token.kind == "string":
            self.take()
            return Literal(text=token.text)

        if token.kind == "json":
            self.take()
            try:
                return JsonLiteral(value=json.loads(token.text))
            except ValueError as error:
                raise ParseError(f"invalid JSON in expression: {token.text}") from error

        if token.kind == "word":
            # An unquoted word is read as JSON, so `true`, `false`, `null` and
            # numbers are those values. Anything else must be quoted.
            self.take()
            try:
                return JsonLiteral(value=json.loads(token.text))
            except ValueError:
                raise ParseError(f"strings must be quoted: {token.text}") from None

        if token.kind == "call":
            self.take()
            node: T.Any = Call(text=token.text)
            while self.peek() is not None and self.peek().kind == "call-args":
                node = CallValue(target=node, args=self.take().text)
            return node

        if token.kind == "reference":
            self.take()
            node: T.Any = ReferenceText(text=token.text)
            following = self.peek()
            if following is not None and following.kind == "curry":
                self.take()
                node = Curry(target=node, text=following.text)
            return node

        raise ParseError(f"unexpected {token.text!r} in expression: {self.source!r}")


def parse_expression(source: str) -> T.Any:
    """Parse a jazzoo expression into a tree.

    Precedence, loosest first: ternary, or, and, not, ==, pipe, path join,
    primary.
    """
    tokens = tokenize_expression(source)
    if not tokens:
        return Literal(text="")
    return _Parser(tokens, source).parse()
