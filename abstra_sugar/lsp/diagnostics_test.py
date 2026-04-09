from lsprotocol import types

from .diagnostics import compute_diagnostics


def test_valid_source_no_diagnostics():
    diags = compute_diagnostics("h1: Hello")
    assert diags == []


def test_undefined_component_warning():
    source = 'card("Users"):'
    diags = compute_diagnostics(source)
    assert len(diags) == 1
    assert diags[0].severity == types.DiagnosticSeverity.Warning
    assert "card" in diags[0].message


def test_defined_component_no_warning():
    source = 'card = (title):\n h1: {title}\ncard("Users"):'
    diags = compute_diagnostics(source)
    assert diags == []
