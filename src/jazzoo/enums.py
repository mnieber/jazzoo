from enum import Enum


class Sigil(Enum):
    GOAT = "🐐"
    MOUSE = "🐭"
    LEOPARD = "🐆"
    SYSTEM = "⚙️"


class BlockMode(Enum):
    # Every line is its own subprocess; the default when no shebang is given.
    JAZZOO = "jazzoo"
    # The whole block is one subprocess running the declared interpreter.
    SHEBANG = "shebang"
