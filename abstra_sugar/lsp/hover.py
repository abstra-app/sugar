import re
from typing import Optional

from lsprotocol import types

from ..parser import HTML_TAGS
from .state import DocumentState


def get_hover(
    state: DocumentState, line: int, character: int,
) -> Optional[types.Hover]:
    lines = state.source.split("\n")
    if line >= len(lines):
        return None
    current_line = lines[line]
    word = _word_at(current_line, character)
    if not word:
        return None

    # Component def
    m = re.match(r"(\s*)(\w+)\s*=\s*\(([^)]*)\)", current_line)
    if m and m.group(2) == word:
        name = m.group(2)
        params = m.group(3)
        return types.Hover(
            contents=types.MarkupContent(
                kind=types.MarkupKind.Markdown,
                value=f"**component** `{name}({params})`",
            ),
        )

    # Component call
    if word in state.components:
        comp = state.components[word]
        params = ", ".join(comp.params)
        def_line = _find_def_line(lines, word)
        loc = f" (line {def_line + 1})" if def_line is not None else ""
        return types.Hover(
            contents=types.MarkupContent(
                kind=types.MarkupKind.Markdown,
                value=f"**component** `{word}({params})`{loc}",
            ),
        )

    # HTML tag
    if word in HTML_TAGS:
        return types.Hover(
            contents=types.MarkupContent(
                kind=types.MarkupKind.Markdown,
                value=f"**HTML element** `<{word}>`",
            ),
        )
    return None


def _word_at(line: str, col: int) -> Optional[str]:
    if col >= len(line):
        return None
    if not line[col:col+1].isalnum() and line[col:col+1] != "_":
        return None
    start = col
    while start > 0 and (line[start - 1].isalnum() or line[start - 1] == "_"):
        start -= 1
    end = col
    while end < len(line) and (line[end].isalnum() or line[end] == "_"):
        end += 1
    return line[start:end] if start < end else None


def _find_def_line(lines: list, name: str) -> Optional[int]:
    pattern = rf"^\s*{re.escape(name)}\s*=\s*\("
    for i, line in enumerate(lines):
        if re.match(pattern, line):
            return i
    return None
