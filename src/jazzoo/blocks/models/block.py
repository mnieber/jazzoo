import typing as T

from dataclassy import dataclass

from jazzoo.enums import BlockMode


@dataclass
class BlockLine:
    text: str
    line: int
    # Set by a leading `@`, which hides the echoed command but not its output.
    is_quiet: bool = False


@dataclass
class Block:
    mode: BlockMode
    # The interpreter line, e.g. "#!/usr/bin/env python3". None in jazzoo mode.
    shebang: T.Optional[str] = None
    lines: T.List[BlockLine] = []
    filename: T.Optional[str] = None
