"""Tests for semantic tokens provider."""

from typing import List, Tuple

from .semantic_tokens import (
    TOKEN_MODIFIERS,
    TOKEN_TYPES,
    get_semantic_tokens,
)


def _all_tokens(source: str) -> List[Tuple[int, int, int, str, List[str]]]:
    """Return all tokens as (line, col, length, type_name, modifiers) tuples."""
    raw = get_semantic_tokens(source)
    result = []
    line = 0
    col = 0
    for i in range(0, len(raw), 5):
        dl, dc, length, ti, mm = raw[i : i + 5]
        if dl > 0:
            line += dl
            col = dc
        else:
            col += dc
        type_name = TOKEN_TYPES[ti]
        mods = [TOKEN_MODIFIERS[j] for j in range(len(TOKEN_MODIFIERS)) if mm & (1 << j)]
        result.append((line, col, length, type_name, mods))
    return result


def _find_tokens(source: str, token_type: str) -> List[Tuple[int, int, int]]:
    """Return all tokens of a given type as (line, col, length) tuples."""
    all_toks = _all_tokens(source)
    return [(line, col, length) for line, col, length, ttype, _ in all_toks if ttype == token_type]


def _find_tokens_with_mods(
    source: str, token_type: str, *modifiers: str
) -> List[Tuple[int, int, int]]:
    """Return tokens matching type and all given modifiers."""
    mod_set = set(modifiers)
    all_toks = _all_tokens(source)
    return [
        (line, col, length)
        for line, col, length, ttype, mods in all_toks
        if ttype == token_type and mod_set.issubset(set(mods))
    ]


# ---- HTML context tests ----


def test_tag_name():
    toks = _find_tokens("div:", "tag")
    assert len(toks) >= 1
    assert toks[0] == (0, 0, 3)  # "div" at col 0


def test_class():
    toks = _find_tokens(".foo:", "class")
    assert len(toks) >= 1


def test_tag_with_class():
    tags = _find_tokens("div.foo:", "tag")
    classes = _find_tokens("div.foo:", "class")
    assert len(tags) >= 1
    assert len(classes) >= 1


def test_id():
    toks = _find_tokens("#bar:", "type")
    assert len(toks) >= 1
    # Should have 'id' modifier
    all_toks = _all_tokens("#bar:")
    id_toks = [(l, c, le, m) for l, c, le, t, m in all_toks if t == "type"]
    assert len(id_toks) >= 1
    assert "id" in id_toks[0][3]


def test_attribute_key_value():
    source = "input type=text:"
    tags = _find_tokens(source, "tag")
    props = _find_tokens(source, "property")
    strings = _find_tokens(source, "string")
    assert len(tags) >= 1
    assert len(props) >= 1
    assert len(strings) >= 1


def test_comment():
    toks = _find_tokens("# hello", "comment")
    assert len(toks) >= 1
    assert toks[0] == (0, 0, 7)


def test_keyword_for():
    source = "for x of items:"
    kws = _find_tokens(source, "keyword")
    # Should have "for" and "of"
    assert len(kws) >= 2


def test_interpolation():
    source = "h1: Hello {name}"
    vars_ = _find_tokens(source, "variable")
    assert len(vars_) >= 1


def test_colon_operator():
    ops = _find_tokens("div:", "operator")
    assert len(ops) >= 1


# ---- CSS context tests ----


def test_css_selector():
    source = "style:\n .foo:\n  color: red"
    classes = _find_tokens(source, "class")
    assert len(classes) >= 1


def test_css_property():
    source = "style:\n .foo:\n  color: red"
    props = _find_tokens(source, "property")
    assert len(props) >= 1


# ---- Script context tests ----


def test_script_function_def():
    source = "script:\n greet(name):\n  return name"
    fns = _find_tokens_with_mods(source, "function", "declaration")
    assert len(fns) >= 1


def test_script_class_def():
    source = "script:\n class Animal:\n  speak():\n   return 'woof'"
    classes = _find_tokens(source, "class")
    assert len(classes) >= 1


def test_script_keyword():
    source = "script:\n for item of items:\n  console.log(item)"
    kws = _find_tokens(source, "keyword")
    assert len(kws) >= 1


def test_script_string():
    source = 'script:\n x = "hello"'
    strings = _find_tokens(source, "string")
    assert len(strings) >= 1


def test_script_number():
    source = "script:\n x = 42"
    nums = _find_tokens(source, "number")
    assert len(nums) >= 1


def test_script_comment():
    source = "script:\n // comment\n x = 1"
    comments = _find_tokens(source, "comment")
    assert len(comments) >= 1


def test_script_builtin():
    source = "script:\n console.log('hi')"
    builtins = _find_tokens_with_mods(source, "variable", "defaultLibrary")
    assert len(builtins) >= 1


def test_script_template_macro():
    source = "script:\n x = html!:\n  h1: Hello"
    macros = _find_tokens(source, "macro")
    assert len(macros) >= 1


def test_component_def():
    source = 'card = (title):\n h1: {title}'
    fns = _find_tokens_with_mods(source, "function", "declaration")
    params = _find_tokens(source, "parameter")
    assert len(fns) >= 1
    assert len(params) >= 1


def test_component_call():
    source = 'card("Users"):'
    fns = _find_tokens(source, "function")
    assert len(fns) >= 1


def test_table_literal_macro():
    source = "table!.striped:"
    macros = _find_tokens(source, "macro")
    assert len(macros) >= 1
