import re
from typing import Optional

from lsprotocol import types

from .state import DocumentState


def get_definition(
    state: DocumentState, line: int, character: int,
) -> Optional[types.Location]:
    lines = state.source.split("\n")
    if line >= len(lines):
        return None
    current_line = lines[line]
    m = re.match(r"(\s*)(\w+)\s*\(", current_line)
    if m:
        name = m.group(2)
        name_start = len(m.group(1))
        name_end = name_start + len(name)
        if name_start <= character <= name_end and name in state.components:
            def_line = _find_component_def_line(lines, name)
            if def_line is not None:
                return types.Location(
                    uri=state.uri,
                    range=types.Range(
                        start=types.Position(line=def_line, character=0),
                        end=types.Position(line=def_line, character=len(lines[def_line])),
                    ),
                )
    return None


def _find_component_def_line(lines: list, name: str) -> Optional[int]:
    pattern = rf"^\s*{re.escape(name)}\s*=\s*\("
    for i, line in enumerate(lines):
        if re.match(pattern, line):
            return i
    return None
