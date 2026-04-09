from typing import List, Optional

from lsprotocol import types

from ..ast import (
    ComponentDef, Element, Node,
    ScriptClass, ScriptElement, ScriptFunction, StyleElement,
)
from .state import DocumentState


def get_document_symbols(state: DocumentState) -> List[types.DocumentSymbol]:
    symbols: List[types.DocumentSymbol] = []
    lines = state.source.split("\n")
    for node in state.ast:
        sym = _node_to_symbol(node, lines)
        if sym is not None:
            symbols.append(sym)
    return symbols


def _node_to_symbol(node: Node, lines: List[str]) -> Optional[types.DocumentSymbol]:
    if isinstance(node, ComponentDef):
        line_num = _find_line(lines, node.name)
        params = ", ".join(node.params)
        return types.DocumentSymbol(
            name=node.name, detail=f"({params})",
            kind=types.SymbolKind.Function,
            range=_line_range(line_num, lines),
            selection_range=_line_range(line_num, lines),
        )
    if isinstance(node, StyleElement):
        line_num = _find_line(lines, "style")
        return types.DocumentSymbol(
            name="style", kind=types.SymbolKind.Module,
            range=_line_range(line_num, lines),
            selection_range=_line_range(line_num, lines),
        )
    if isinstance(node, ScriptElement):
        line_num = _find_line(lines, "script")
        children: List[types.DocumentSymbol] = []
        for sn in node.body_nodes:
            child = _script_node_to_symbol(sn, lines)
            if child:
                children.append(child)
        return types.DocumentSymbol(
            name="script", kind=types.SymbolKind.Module,
            range=_line_range(line_num, lines),
            selection_range=_line_range(line_num, lines),
            children=children if children else None,
        )
    if isinstance(node, Element):
        line_num = _find_line(lines, node.tag)
        children = []
        for child in node.children:
            sym = _node_to_symbol(child, lines)
            if sym:
                children.append(sym)
        return types.DocumentSymbol(
            name=node.tag, kind=types.SymbolKind.Class,
            range=_line_range(line_num, lines),
            selection_range=_line_range(line_num, lines),
            children=children if children else None,
        )
    return None


def _script_node_to_symbol(node, lines: List[str]) -> Optional[types.DocumentSymbol]:
    if isinstance(node, ScriptFunction):
        if not node.name:
            return None
        line_num = _find_line(lines, node.name)
        params = ", ".join(node.params)
        return types.DocumentSymbol(
            name=node.name, detail=f"({params})",
            kind=types.SymbolKind.Function,
            range=_line_range(line_num, lines),
            selection_range=_line_range(line_num, lines),
        )
    if isinstance(node, ScriptClass):
        line_num = _find_line(lines, f"class {node.name}")
        children = []
        for method in node.methods:
            child = _script_node_to_symbol(method, lines)
            if child:
                children.append(child)
        return types.DocumentSymbol(
            name=node.name,
            detail=f"extends {node.extends}" if node.extends else None,
            kind=types.SymbolKind.Class,
            range=_line_range(line_num, lines),
            selection_range=_line_range(line_num, lines),
            children=children if children else None,
        )
    return None


def _find_line(lines: List[str], needle: str) -> int:
    for i, line in enumerate(lines):
        if needle in line:
            return i
    return 0


def _line_range(line_num: int, lines: List[str]) -> types.Range:
    length = len(lines[line_num]) if line_num < len(lines) else 0
    return types.Range(
        start=types.Position(line=line_num, character=0),
        end=types.Position(line=line_num, character=length),
    )
