from ..ast import Element, ScriptElement, StyleElement
from .state import DocumentState


def test_parse_simple_document():
    state = DocumentState("file:///test.sugar", "h1: Hello")
    assert len(state.ast) == 1
    assert isinstance(state.ast[0], Element)
    assert state.ast[0].tag == "h1"
    assert state.diagnostics == []


def test_parse_with_components():
    source = "card = (title):\n h1: {title}\ncard(\"Users\"):"
    state = DocumentState("file:///test.sugar", source)
    assert "card" in state.components


def test_update_source():
    state = DocumentState("file:///test.sugar", "h1: Hello")
    assert state.ast[0].tag == "h1"
    state.update("p: World")
    assert state.ast[0].tag == "p"


def test_parse_error_produces_diagnostic():
    state = DocumentState("file:///test.sugar", "h1: Hello")
    assert state.diagnostics == []


def test_style_block():
    source = "style:\n .foo:\n  color: red"
    state = DocumentState("file:///test.sugar", source)
    assert len(state.ast) == 1
    assert isinstance(state.ast[0], StyleElement)


def test_script_block():
    source = "script:\n x = 1"
    state = DocumentState("file:///test.sugar", source)
    assert len(state.ast) == 1
    assert isinstance(state.ast[0], ScriptElement)
    assert len(state.ast[0].body_nodes) == 1
