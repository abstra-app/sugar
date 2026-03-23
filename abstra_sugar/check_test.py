from .check import check_source

# --- explicit div ---


def test_div_with_class():
    w = check_source("div.foo:")
    assert len(w) == 1
    assert w[0]["level"] == "warning"
    assert w[0]["line"] == 1
    assert "div is implicit" in w[0]["message"]
    assert "'.foo'" in w[0]["message"]


def test_div_with_id():
    w = check_source("div#main:")
    assert len(w) == 1
    assert "'#main'" in w[0]["message"]


def test_div_with_class_and_id():
    w = check_source("div#app.container:")
    assert len(w) == 1
    assert "'#app.container'" in w[0]["message"]


def test_plain_div_no_warning():
    assert check_source("div:") == []


def test_implicit_div_no_warning():
    assert check_source(".foo:") == []
    assert check_source("#main:") == []


# --- implicit children ---


def test_li_inside_ul():
    w = check_source("ul:\n li: Item")
    assert len(w) == 1
    assert w[0]["level"] == "warning"
    assert "'li' is implicit inside 'ul'" in w[0]["message"]
    assert "': Item'" in w[0]["message"]


def test_li_inside_ol():
    w = check_source("ol:\n li: First")
    assert len(w) == 1
    assert "'li' is implicit inside 'ol'" in w[0]["message"]


def test_option_inside_select():
    w = check_source("select:\n option value=x: X")
    assert len(w) == 1
    assert "'option' is implicit inside 'select'" in w[0]["message"]


def test_td_inside_tr():
    w = check_source("tr:\n td: Cell")
    assert len(w) == 1
    assert "'td' is implicit inside 'tr'" in w[0]["message"]


def test_th_inside_thead():
    w = check_source("thead:\n th: Header")
    assert len(w) == 1
    assert "'th' is implicit inside 'thead'" in w[0]["message"]


def test_implicit_child_with_class():
    w = check_source("ul:\n li.active: Item")
    assert len(w) == 1
    assert "'.active'" in w[0]["message"]


def test_implicit_child_no_warning():
    assert check_source("ul:\n : Item") == []
    assert check_source("select:\n value=x: X") == []
    assert check_source("tr:\n : Cell") == []


# --- script blocks skipped ---


def test_no_warning_inside_script():
    assert check_source("script:\n div.foo = 1") == []
    assert check_source("script:\n div.innerHTML = ''") == []


def test_no_warning_nested_script():
    code = "html:\n body:\n  script:\n   div.classList.add('x')"
    assert check_source(code) == []


# --- no false positives ---


def test_no_warning_for_normal_elements():
    assert check_source("h1: Title") == []
    assert check_source("p.intro: Hello") == []
    assert check_source("a href=/about: Link") == []


def test_no_warning_for_non_implicit_parent():
    assert check_source("div:\n li: Item") == []
    assert check_source("span:\n option: X") == []


def test_multiple_warnings():
    code = "div.foo:\n ul:\n  li: A\n  li: B"
    w = check_source(code)
    assert len(w) == 3
    assert all(d["level"] == "warning" for d in w)


# --- inline objects in script ---


def test_inline_object_warning():
    w = check_source("script:\n x = {a: 1, b: 2}")
    assert len(w) == 1
    assert "inline object" in w[0]["message"]
    assert "indented notation" in w[0]["message"]


def test_inline_nested_object_warning():
    w = check_source("script:\n x = {a: 1, b: {c: 2}}")
    assert len(w) >= 1
    assert any("inline object" in d["message"] for d in w)


def test_empty_object_no_warning():
    assert check_source("script:\n x = {}") == []


def test_template_literal_no_warning():
    assert check_source("script:\n s = `${name}`") == []


# --- inline arrays in script ---


def test_inline_array_warning():
    w = check_source("script:\n x = [1, 2, 3]")
    assert len(w) == 1
    assert "inline list" in w[0]["message"]
    assert "indented notation" in w[0]["message"]


def test_empty_array_no_warning():
    assert check_source("script:\n x = []") == []


def test_array_access_no_warning():
    assert check_source("script:\n x = arr[0]") == []
    assert check_source("script:\n x = obj[key]") == []


def test_single_element_array_no_warning():
    # [1] has no comma, not flagged
    assert check_source("script:\n x = [1]") == []


# --- mixed ---


def test_object_and_array_same_line():
    w = check_source("script:\n x = {items: [1, 2]}")
    assert len(w) >= 1
    assert any("inline object" in d["message"] for d in w)


# --- trailing semicolons ---


def test_semicolon_warning():
    w = check_source("script:\n x = 1;")
    assert len(w) == 1
    assert "semicolons are unnecessary" in w[0]["message"]


def test_no_semicolon_no_warning():
    assert check_source("script:\n x = 1") == []


# --- arrow functions ---


def test_arrow_function_warning():
    w = check_source("script:\n arr.map((x) => x + 1)")
    assert len(w) == 1
    assert "() =>" in w[0]["message"]
    assert "():" in w[0]["message"]


def test_sugar_arrow_no_warning():
    assert check_source("script:\n arr.map((x): x + 1)") == []


# --- function keyword ---


def test_function_keyword_warning():
    w = check_source("script:\n function add(a, b) { return a + b }")
    assert len(w) >= 1
    assert any("function name()" in d["message"] for d in w)


def test_anon_function_warning():
    w = check_source("script:\n setTimeout(function() { return 1 })")
    assert len(w) >= 1
    assert any("function()" in d["message"] for d in w)


def test_sugar_function_no_warning():
    # Sugar-style function: name():
    assert check_source("script:\n add(a, b):\n  return a + b") == []
