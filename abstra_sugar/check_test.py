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
    w = check_source("ul:\n\tli: Item")
    assert len(w) == 1
    assert w[0]["level"] == "warning"
    assert "'li' is implicit inside 'ul'" in w[0]["message"]
    assert "': Item'" in w[0]["message"]


def test_li_inside_ol():
    w = check_source("ol:\n\tli: First")
    assert len(w) == 1
    assert "'li' is implicit inside 'ol'" in w[0]["message"]


def test_option_inside_select():
    w = check_source("select:\n\toption value=x: X")
    assert len(w) == 1
    assert "'option' is implicit inside 'select'" in w[0]["message"]


def test_td_inside_tr():
    w = check_source("tr:\n\ttd: Cell")
    assert len(w) == 1
    assert "'td' is implicit inside 'tr'" in w[0]["message"]


def test_th_inside_thead():
    w = check_source("thead:\n\tth: Header")
    assert len(w) == 1
    assert "'th' is implicit inside 'thead'" in w[0]["message"]


def test_implicit_child_with_class():
    w = check_source("ul:\n\tli.active: Item")
    assert len(w) == 1
    assert "'.active'" in w[0]["message"]


def test_implicit_child_no_warning():
    assert check_source("ul:\n\t: Item") == []
    assert check_source("select:\n\tvalue=x: X") == []
    assert check_source("tr:\n\t: Cell") == []


# --- script blocks skipped ---


def test_no_warning_inside_script():
    assert check_source("script:\n\tdiv.foo = 1") == []
    assert check_source("script:\n\tdiv.innerHTML = ''") == []


def test_no_warning_nested_script():
    code = "html:\n\tbody:\n\t\tscript:\n\t\t\tdiv.classList.add('x')"
    assert check_source(code) == []


# --- no false positives ---


def test_no_warning_for_normal_elements():
    assert check_source("h1: Title") == []
    assert check_source("p.intro: Hello") == []
    assert check_source("a href=/about: Link") == []


def test_no_warning_for_non_implicit_parent():
    assert check_source("div:\n\tli: Item") == []
    assert check_source("span:\n\toption: X") == []


def test_multiple_warnings():
    code = "div.foo:\n\tul:\n\t\tli: A\n\t\tli: B"
    w = check_source(code)
    assert len(w) == 3
    assert all(d["level"] == "warning" for d in w)
