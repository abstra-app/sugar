from .definition import get_definition
from .state import DocumentState


def test_component_call_to_def():
    source = 'card = (title):\n h1: {title}\ncard("Users"):'
    state = DocumentState("file:///t.sugar", source)
    result = get_definition(state, 2, 0)
    assert result is not None
    assert result.range.start.line == 0


def test_unknown_name_no_result():
    source = 'unknown("x"):'
    state = DocumentState("file:///t.sugar", source)
    result = get_definition(state, 0, 0)
    assert result is None


def test_cursor_not_on_component():
    state = DocumentState("file:///t.sugar", "h1: Hello")
    result = get_definition(state, 0, 0)
    assert result is None
