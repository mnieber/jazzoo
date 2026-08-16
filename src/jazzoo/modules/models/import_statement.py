import typing as T

from dataclassy import dataclass


@dataclass
class ImportedSymbol:
    name: str
    # The name it is bound under, which differs from `name` only for `x as y`.
    alias: str


@dataclass
class ImportStatement:
    # The path as written in the .jaz file, always explicit relative or absolute.
    path: str
    # Empty means `*` - every symbol the imported module exports.
    symbols: T.List[ImportedSymbol] = []
    is_wildcard: bool = False
    # `export` lands symbols flat in 🐭 and makes them targets; `import` namespaces
    # them under `alias` and keeps them private.
    is_export: bool = False
    # The `as <namespace>` alias, mandatory for import and absent for export.
    alias: T.Optional[str] = None
    filename: T.Optional[str] = None
    line: T.Optional[int] = None
