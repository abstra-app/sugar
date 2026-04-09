from .ast import (
    ScriptCatch,
    ScriptClass,
    ScriptCollection,
    ScriptComment,
    ScriptElse,
    ScriptElseIf,
    ScriptFinally,
    ScriptForLoop,
    ScriptFunction,
    ScriptIf,
    ScriptStatement,
    ScriptTemplateLiteral,
    ScriptTry,
    ScriptWhileLoop,
)
from .script_parser import parse_script


# Functions
def test_function_def():
    nodes = parse_script("greet(name):\n return 'hello ' + name")
    assert len(nodes) == 1
    fn = nodes[0]
    assert isinstance(fn, ScriptFunction)
    assert fn.name == "greet"
    assert fn.params == ["name"]
    assert fn.is_async is False
    assert len(fn.body) == 1
    assert isinstance(fn.body[0], ScriptStatement)


def test_async_function():
    nodes = parse_script("async fetchData(url):\n return await fetch(url)")
    fn = nodes[0]
    assert isinstance(fn, ScriptFunction)
    assert fn.is_async is True


def test_function_no_args():
    nodes = parse_script("init():\n console.log('ready')")
    fn = nodes[0]
    assert isinstance(fn, ScriptFunction)
    assert fn.params == []


# Classes
def test_class_def():
    body = "class Animal:\n constructor(name):\n  this.name = name\n speak():\n  return this.name"
    nodes = parse_script(body)
    cls = nodes[0]
    assert isinstance(cls, ScriptClass)
    assert cls.name == "Animal"
    assert cls.extends is None
    assert len(cls.methods) == 2


def test_class_extends():
    nodes = parse_script("class Dog extends Animal:\n speak():\n  return 'woof'")
    cls = nodes[0]
    assert isinstance(cls, ScriptClass)
    assert cls.extends == "Animal"


# Loops
def test_for_of():
    nodes = parse_script("for item of items:\n console.log(item)")
    loop = nodes[0]
    assert isinstance(loop, ScriptForLoop)
    assert loop.var == "item"
    assert loop.keyword == "of"
    assert loop.iterable == "items"


def test_for_in():
    nodes = parse_script("for key in obj:\n console.log(key)")
    assert isinstance(nodes[0], ScriptForLoop)
    assert nodes[0].keyword == "in"


def test_while():
    nodes = parse_script("while i < 5:\n console.log(i)\n i++")
    loop = nodes[0]
    assert isinstance(loop, ScriptWhileLoop)
    assert loop.condition == "i < 5"
    assert len(loop.body) == 2


# Conditionals
def test_if_else_if_else():
    body = "if x > 100:\n return 'big'\nelse if x > 10:\n return 'medium'\nelse:\n return 'small'"
    nodes = parse_script(body)
    assert len(nodes) == 3
    assert isinstance(nodes[0], ScriptIf)
    assert isinstance(nodes[1], ScriptElseIf)
    assert isinstance(nodes[2], ScriptElse)


# Try/catch/finally
def test_try_catch_finally():
    body = "try:\n JSON.parse(input)\ncatch(e):\n console.error(e)\nfinally:\n cleanup()"
    nodes = parse_script(body)
    assert len(nodes) == 3
    assert isinstance(nodes[0], ScriptTry)
    assert isinstance(nodes[1], ScriptCatch)
    assert nodes[1].param == "e"
    assert isinstance(nodes[2], ScriptFinally)


# Comments and statements
def test_comment():
    nodes = parse_script("// this is a comment\nx = 1")
    assert isinstance(nodes[0], ScriptComment)
    assert nodes[0].text == "this is a comment"
    assert isinstance(nodes[1], ScriptStatement)


def test_plain_statement():
    nodes = parse_script("console.log('hello')")
    assert isinstance(nodes[0], ScriptStatement)


# Collections
def test_flat_object():
    nodes = parse_script("point =:\n x: 10\n y: 20")
    coll = nodes[0]
    assert isinstance(coll, ScriptCollection)
    assert coll.lhs == "point"
    assert coll.value == "{x: 10, y: 20}"


def test_array():
    nodes = parse_script('colors =:\n "red"\n "green"\n "blue"')
    coll = nodes[0]
    assert isinstance(coll, ScriptCollection)
    assert coll.value == '["red", "green", "blue"]'


def test_array_of_objects():
    nodes = parse_script(
        'users =:\n :\n  name: "Alice"\n  age: 30\n :\n  name: "Bob"\n  age: 25'
    )
    coll = nodes[0]
    assert isinstance(coll, ScriptCollection)
    assert coll.value == '[{name: "Alice", age: 30}, {name: "Bob", age: 25}]'


def test_nested_object():
    nodes = parse_script('config = theme:\n primary: "#fff"\n secondary: "#000"')
    coll = nodes[0]
    assert isinstance(coll, ScriptCollection)
    assert coll.value == '{theme: {primary: "#fff", secondary: "#000"}}'


# Template literals
def test_template_html():
    nodes = parse_script("app.innerHTML = html!:\n h1: Hello {name}")
    tmpl = nodes[0]
    assert isinstance(tmpl, ScriptTemplateLiteral)
    assert tmpl.prefix == "app.innerHTML = "
    assert tmpl.literal_type == "html!"
    assert "${name}" in tmpl.content


def test_template_text():
    nodes = parse_script("greeting = text!:\n Hello, world!\n No quotes needed.")
    tmpl = nodes[0]
    assert isinstance(tmpl, ScriptTemplateLiteral)
    assert tmpl.literal_type == "text!"
    assert "Hello, world!" in tmpl.content


# Mixed
def test_mixed_statements_and_blocks():
    nodes = parse_script("x = 1\ngreet(name):\n return name\ny = 2")
    assert len(nodes) == 3
    assert isinstance(nodes[0], ScriptStatement)
    assert isinstance(nodes[1], ScriptFunction)
    assert isinstance(nodes[2], ScriptStatement)
