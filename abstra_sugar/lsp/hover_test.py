from .hover import get_hover
from .state import DocumentState


def test_hover_on_html_tag():
    state = DocumentState("file:///t.sugar", "div:")
    result = get_hover(state, 0, 0)
    assert result is not None
    assert "div" in result.contents.value


def test_hover_on_component_call():
    source = 'card = (title):\n h1: {title}\ncard("Users"):'
    state = DocumentState("file:///t.sugar", source)
    result = get_hover(state, 2, 0)
    assert result is not None
    assert "card" in result.contents.value
    assert "title" in result.contents.value


def test_hover_on_component_def():
    source = "card = (title, subtitle):\n h1: {title}"
    state = DocumentState("file:///t.sugar", source)
    result = get_hover(state, 0, 0)
    assert result is not None
    assert "card" in result.contents.value


def test_hover_on_nothing():
    state = DocumentState("file:///t.sugar", "")
    result = get_hover(state, 0, 0)
    assert result is None
