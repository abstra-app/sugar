from lsprotocol import types

from .state import DocumentState
from .symbols import get_document_symbols


def test_top_level_elements():
    state = DocumentState("file:///t.sugar", "html:\n head:\n body:")
    symbols = get_document_symbols(state)
    names = [s.name for s in symbols]
    assert "html" in names


def test_component_symbols():
    source = "card = (title):\n h1: {title}"
    state = DocumentState("file:///t.sugar", source)
    symbols = get_document_symbols(state)
    assert len(symbols) >= 1
    assert symbols[0].name == "card"
    assert symbols[0].kind == types.SymbolKind.Function


def test_style_symbol():
    source = "style:\n .foo:\n  color: red"
    state = DocumentState("file:///t.sugar", source)
    symbols = get_document_symbols(state)
    assert len(symbols) >= 1
    assert symbols[0].name == "style"


def test_script_functions():
    source = "script:\n greet(name):\n  return name\n init():\n  console.log('ok')"
    state = DocumentState("file:///t.sugar", source)
    symbols = get_document_symbols(state)
    assert len(symbols) >= 1
    script_sym = symbols[0]
    assert script_sym.name == "script"
