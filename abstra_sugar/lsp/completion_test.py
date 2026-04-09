from .completion import get_completions
from .state import DocumentState


def test_html_tag_completion():
    state = DocumentState("file:///t.sugar", "di")
    items = get_completions(state, 0, 2)
    labels = [i.label for i in items]
    assert "div" in labels


def test_keyword_completion():
    state = DocumentState("file:///t.sugar", "fo")
    items = get_completions(state, 0, 2)
    labels = [i.label for i in items]
    assert "for" in labels


def test_component_completion():
    source = "card = (title):\n h1: {title}\nca"
    state = DocumentState("file:///t.sugar", source)
    items = get_completions(state, 2, 2)
    labels = [i.label for i in items]
    assert "card" in labels


def test_attribute_value_completion():
    state = DocumentState("file:///t.sugar", "input type=")
    items = get_completions(state, 0, 11)
    labels = [i.label for i in items]
    assert "text" in labels


def test_style_property_completion():
    source = "style:\n .foo:\n  col"
    state = DocumentState("file:///t.sugar", source)
    items = get_completions(state, 2, 5)
    labels = [i.label for i in items]
    assert "color" in labels
