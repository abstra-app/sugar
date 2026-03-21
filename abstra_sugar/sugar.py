import warnings as _warnings
from typing import Optional

from .compiler import compile
from .lexer import scan
from .parser import parse
from .check import _check_tokens


def sugar(text: str, data: Optional[dict] = None) -> str:
    tokens = scan(text)
    for d in _check_tokens(tokens):
        _warnings.warn(
            f"line {d['line']}: {d['message']}", SugarWarning, stacklevel=2
        )
    nodes = parse(tokens)
    return compile(nodes, data)


class SugarWarning(UserWarning):
    pass
