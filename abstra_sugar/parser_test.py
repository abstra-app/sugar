from .ast import Element, ScriptElement, StyleElement, StyleRule
from .lexer import scan
from .parser import parse, parse_inline


def test_simple_element():
    nodes = parse(scan("html:"))
    assert len(nodes) == 1
    assert isinstance(nodes[0], Element)
    assert nodes[0].tag == "html"


def test_element_with_class():
    nodes = parse(scan("thead.table-header:"))
    el = nodes[0]
    assert isinstance(el, Element)
    assert el.tag == "thead"
    assert el.classes == ["table-header"]


def test_element_with_attr():
    nodes = parse(scan("tr onmouseover=mousehover(this) :"))
    el = nodes[0]
    assert isinstance(el, Element)
    assert el.tag == "tr"
    assert el.attributes == {"onmouseover": "mousehover(this)"}


def test_element_with_text():
    nodes = parse(scan("h1: Users"))
    el = nodes[0]
    assert isinstance(el, Element)
    assert el.text == "Users"


def test_nested_elements():
    nodes = parse(scan("div:\n p: hello"))
    div = nodes[0]
    assert isinstance(div, Element)
    assert len(div.children) == 1
    p = div.children[0]
    assert isinstance(p, Element)
    assert p.tag == "p"
    assert p.text == "hello"


def test_boolean_attr():
    nodes = parse(scan("script module:"))
    assert isinstance(nodes[0], ScriptElement)
    assert nodes[0].attributes == {"module": True}


def test_style_block():
    source = "style:\n .table-header:\n  font-weight: bold"
    nodes = parse(scan(source))
    assert isinstance(nodes[0], StyleElement)
    assert len(nodes[0].rules) == 1
    rule = nodes[0].rules[0]
    assert rule.selector == ".table-header"
    assert rule.properties == [("font-weight", "bold")]


def test_script_block():
    source = "script:\n console.log(t)"
    nodes = parse(scan(source))
    assert isinstance(nodes[0], ScriptElement)
    assert nodes[0].body == "console.log(t)"


def test_script_block_raw():
    source = "script:\n if x > 0:\n  console.log(x)"
    nodes = parse(scan(source))
    script = nodes[0]
    assert isinstance(script, ScriptElement)
    assert "if x > 0:" in script.body
    assert " console.log(x)" in script.body


def test_parse_inline():
    el = parse_inline("a href=/users/1: Edit User")
    assert el is not None
    assert el.tag == "a"
    assert el.attributes == {"href": "/users/1"}
    assert el.text == "Edit User"


def test_parse_inline_not_element():
    assert parse_inline("just some text") is None
    assert parse_inline("link") is None
    assert parse_inline("foo@company.com") is None
