from typing import Dict, List

from lsprotocol import types

from ..ast import ComponentCall, ComponentDef, Element, Node
from ..lexer import scan
from ..parser import parse


def compute_diagnostics(source: str) -> List[types.Diagnostic]:
    diagnostics: List[types.Diagnostic] = []
    try:
        tokens = scan(source)
        ast = parse(tokens)
    except Exception as e:
        diagnostics.append(
            types.Diagnostic(
                range=types.Range(
                    start=types.Position(line=0, character=0),
                    end=types.Position(line=0, character=0),
                ),
                message=str(e),
                severity=types.DiagnosticSeverity.Error,
                source="sugar",
            )
        )
        return diagnostics

    components: Dict[str, ComponentDef] = {}
    _collect_components(ast, components)
    _check_undefined_calls(ast, components, diagnostics, source)
    return diagnostics


def _collect_components(nodes: List[Node], components: Dict[str, ComponentDef]) -> None:
    for node in nodes:
        if isinstance(node, ComponentDef):
            components[node.name] = node
        elif isinstance(node, Element):
            _collect_components(node.children, components)


def _check_undefined_calls(
    nodes: List[Node], components: Dict[str, ComponentDef],
    diagnostics: List[types.Diagnostic], source: str,
) -> None:
    lines = source.split("\n")
    for node in nodes:
        if isinstance(node, ComponentCall):
            if node.name not in components:
                line_num = _find_line(lines, node.name + "(")
                diagnostics.append(
                    types.Diagnostic(
                        range=types.Range(
                            start=types.Position(line=line_num, character=0),
                            end=types.Position(line=line_num, character=len(lines[line_num]) if line_num < len(lines) else 0),
                        ),
                        message=f"Undefined component '{node.name}'",
                        severity=types.DiagnosticSeverity.Warning,
                        source="sugar",
                    )
                )
        elif isinstance(node, Element):
            _check_undefined_calls(node.children, components, diagnostics, source)
        elif isinstance(node, ComponentDef):
            _check_undefined_calls(node.children, components, diagnostics, source)


def _find_line(lines: List[str], needle: str) -> int:
    for i, line in enumerate(lines):
        if needle in line:
            return i
    return 0
