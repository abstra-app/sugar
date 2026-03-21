from .compiler import compile
from .lexer import scan
from .parser import parse


def sugar(text: str) -> str:
    tokens = scan(text)
    nodes = parse(tokens)
    return compile(nodes)
