from .lexer import scan
from .tokens import Token


def test_simple_element():
    tokens = scan("html:")
    assert tokens == [Token("line", 0, "html", "", True)]


def test_element_with_text():
    tokens = scan("h1: Users")
    assert tokens == [Token("line", 0, "h1", "Users", True)]


def test_indentation():
    tokens = scan("html:\n\thead:")
    assert tokens == [
        Token("line", 0, "html", "", True),
        Token("line", 1, "head", "", True),
    ]


def test_no_colon():
    tokens = scan("\t\tconsole.log(t)")
    assert tokens == [Token("line", 2, "console.log(t)", "", False)]


def test_colon_in_parens():
    tokens = scan("tr onmouseover=mousehover(this) :")
    assert tokens == [
        Token("line", 0, "tr onmouseover=mousehover(this)", "", True),
    ]


def test_blank_lines():
    tokens = scan("a:\n\nb:")
    assert tokens == [
        Token("line", 0, "a", "", True),
        Token("blank", 0, "", "", False),
        Token("line", 0, "b", "", True),
    ]


def test_style_property():
    tokens = scan("\t\t\tfont-weight: bold")
    assert tokens == [Token("line", 3, "font-weight", "bold", True)]


def test_inline_element_text():
    tokens = scan("td: a href=/users/1: Edit User")
    assert tokens == [
        Token("line", 0, "td", "a href=/users/1: Edit User", True),
    ]


def test_comments():
    tokens = scan("div:\n\t# This is a comment\n\tp: hello")
    assert tokens == [
        Token("line", 0, "div", "", True),
        Token("comment", 1, "# This is a comment", "", False),
        Token("line", 1, "p", "hello", True),
    ]
