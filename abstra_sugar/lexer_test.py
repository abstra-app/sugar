from .lexer import scan
from .tokens import Token


def test_simple_element():
    tokens = scan("html:")
    assert tokens == [Token("line", 0, "html", "", True)]


def test_element_with_text():
    tokens = scan("h1: Users")
    assert tokens == [Token("line", 0, "h1", "Users", True)]


def test_indentation():
    tokens = scan("html:\n head:")
    assert tokens == [
        Token("line", 0, "html", "", True),
        Token("line", 1, "head", "", True),
    ]


def test_no_colon():
    tokens = scan("  console.log(t)")
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
    tokens = scan("   font-weight: bold")
    assert tokens == [Token("line", 3, "font-weight", "bold", True)]


def test_inline_element_text():
    tokens = scan("td: a href=/users/1: Edit User")
    assert tokens == [
        Token("line", 0, "td", "a href=/users/1: Edit User", True),
    ]


def test_comments():
    tokens = scan("div:\n # This is a comment\n p: hello")
    assert tokens == [
        Token("line", 0, "div", "", True),
        Token("comment", 1, "# This is a comment", "", False),
        Token("line", 1, "p", "hello", True),
    ]


# --- string tracking ---


def test_colon_in_double_quoted_string():
    tokens = scan('div title="10:30 AM":')
    assert tokens == [Token("line", 0, 'div title="10:30 AM"', "", True)]


def test_colon_in_single_quoted_string():
    tokens = scan("div title='10:30 AM':")
    assert tokens == [Token("line", 0, "div title='10:30 AM'", "", True)]


def test_colon_in_string_with_text():
    tokens = scan('span title="time: now": Hello')
    assert tokens == [Token("line", 0, 'span title="time: now"', "Hello", True)]


# --- brace/bracket tracking ---


def test_colon_in_braces():
    tokens = scan("button onclick=handle({delay: 100}):")
    assert tokens == [
        Token("line", 0, "button onclick=handle({delay: 100})", "", True),
    ]


def test_colon_in_brackets():
    tokens = scan("div data=[{a: 1}]:")
    assert tokens == [Token("line", 0, "div data=[{a: 1}]", "", True)]


# --- mailto and other non-// URLs ---


def test_mailto_url():
    tokens = scan("a href=mailto:user@test.com: Send")
    assert tokens == [
        Token("line", 0, "a href=mailto:user@test.com", "Send", True),
    ]
