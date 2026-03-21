from typing import Optional

from .compiler import compile
from .lexer import scan
from .parser import parse


def sugar(text: str, data: Optional[dict] = None) -> str:
    tokens = scan(text)
    nodes = parse(tokens)
    return compile(nodes, data)
