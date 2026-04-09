from typing import Dict, List

from lsprotocol import types

from ..ast import ComponentDef, Node
from ..lexer import scan
from ..parser import parse
from ..tokens import Token


class DocumentState:
    def __init__(self, uri: str, source: str):
        self.uri = uri
        self.source = source
        self.tokens: List[Token] = []
        self.ast: List[Node] = []
        self.components: Dict[str, ComponentDef] = {}
        self.diagnostics: List[types.Diagnostic] = []
        self._parse()

    def update(self, source: str) -> None:
        self.source = source
        self._parse()

    def _parse(self) -> None:
        self.diagnostics = []
        try:
            self.tokens = scan(self.source)
            self.ast = parse(self.tokens)
            self.components = self._collect_components(self.ast)
            from .diagnostics import compute_diagnostics
            self.diagnostics = compute_diagnostics(self.source)
        except Exception as e:
            self.ast = []
            self.components = {}
            self.diagnostics.append(
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

    def _collect_components(self, nodes: List[Node]) -> Dict[str, ComponentDef]:
        components: Dict[str, ComponentDef] = {}
        for node in nodes:
            if isinstance(node, ComponentDef):
                components[node.name] = node
        return components
