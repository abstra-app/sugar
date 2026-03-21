from typing import Dict, List, Optional, Tuple, Union

import re

from .ast import (
    ComponentCall, ComponentDef, Element, ForBlock, IfBlock, Node,
    ScriptElement, StyleElement, StyleRule,
)
from .tokens import Token

HTML_TAGS = {
    "a", "abbr", "address", "article", "aside", "audio", "b", "bdi", "bdo",
    "blockquote", "body", "br", "button", "canvas", "caption", "cite", "code",
    "col", "colgroup", "data", "datalist", "dd", "del", "details", "dfn",
    "dialog", "div", "dl", "dt", "em", "embed", "fieldset", "figcaption",
    "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "head",
    "header", "hgroup", "hr", "html", "i", "iframe", "img", "input", "ins",
    "kbd", "label", "legend", "li", "link", "main", "map", "mark", "menu",
    "meta", "meter", "nav", "noscript", "object", "ol", "optgroup", "option",
    "output", "p", "picture", "pre", "progress", "q", "rp", "rt", "ruby",
    "s", "samp", "script", "section", "select", "slot", "small", "source",
    "span", "strong", "style", "sub", "summary", "sup", "table", "tbody",
    "td", "template", "textarea", "tfoot", "th", "thead", "time", "title",
    "tr", "track", "u", "ul", "var", "video", "wbr",
}


def parse(tokens: List[Token]) -> List[Node]:
    segments = _split_script_segments(tokens)
    tree = _build_tree(segments)
    return [_parse_node(item) for item in tree]


# --- script segment extraction ---


def _split_script_segments(tokens: List[Token]) -> List[Token]:
    """Replace script children with a single token containing raw body."""
    result: List[Token] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.type != "line":
            i += 1
            continue

        parts = _split_respecting_parens(token.head)
        tag = parts[0].split(".")[0] if parts and parts[0] else ""
        if tag != "script":
            result.append(token)
            i += 1
            continue

        result.append(token)
        script_indent = token.indent
        i += 1

        body_lines: List[str] = []
        base_indent = script_indent + 1

        while i < len(tokens):
            t = tokens[i]
            if t.type == "line" and t.indent <= script_indent:
                break
            if t.type == "blank":
                body_lines.append("")
            elif t.type == "comment":
                pass
            elif t.type == "line":
                prefix = "\t" * (t.indent - base_indent)
                if t.has_colon and t.text:
                    body_lines.append(f"{prefix}{t.head}: {t.text}")
                elif t.has_colon:
                    body_lines.append(f"{prefix}{t.head}:")
                else:
                    body_lines.append(f"{prefix}{t.head}")
            i += 1

        # trim trailing blank lines
        while body_lines and body_lines[-1] == "":
            body_lines.pop()

        body = "\n".join(body_lines)
        result.append(Token("script_body", script_indent + 1, body, "", False))

    return result


# --- tree building from indent levels ---


def _build_tree(tokens: List[Token]) -> list:
    root: list = []
    stack: List[Tuple[int, dict]] = []

    for token in tokens:
        if token.type in ("blank", "comment"):
            continue

        item = {"token": token, "children": []}

        while stack and stack[-1][0] >= token.indent:
            stack.pop()

        if stack:
            stack[-1][1]["children"].append(item)
        else:
            root.append(item)

        stack.append((token.indent, item))

    return root


IMPLICIT_CHILDREN = {
    "ul": "li",
    "ol": "li",
    "select": "option",
    "datalist": "option",
    "dl": "dt",
    "tr": "td",
    "thead": "th",
    "menu": "li",
}


# --- node classification ---


def _parse_node(item: dict, parent_tag: str = "") -> Node:
    token: Token = item["token"]
    children: list = item["children"]

    # component definition: name = (params):
    m = re.match(r"(\w+)\s*=\s*\(([^)]*)\)$", token.head)
    if m and token.has_colon:
        name, params_str = m.groups()
        params = [p.strip() for p in params_str.split(",") if p.strip()]
        child_nodes = [_parse_node(c) for c in children]
        return ComponentDef(name=name, params=params, children=child_nodes)

    # component call: name(args) where name is not an HTML tag
    m = re.match(r"(\w+)\s*\(([^)]*)\)$", token.head)
    if m and m.group(1) not in HTML_TAGS:
        name = m.group(1)
        args_raw = m.group(2)
        child_nodes = [_parse_node(c) for c in children]
        return ComponentCall(name=name, args_raw=args_raw, children=child_nodes)

    # for/if blocks in HTML context
    m = re.match(r"for\s+(.+?)\s+(of|in)\s+(.+)", token.head)
    if m:
        var, keyword, iterable = m.groups()
        child_nodes = [_parse_node(c, parent_tag) for c in children]
        return ForBlock(var=var, keyword=keyword, iterable=iterable, children=child_nodes)

    if token.head.startswith("if "):
        condition = token.head[3:].strip()
        child_nodes = [_parse_node(c, parent_tag) for c in children]
        return IfBlock(condition=condition, children=child_nodes)

    # implicit child tag: empty head, .class, #id, or attr-only inherits from parent
    head = token.head
    if parent_tag in IMPLICIT_CHILDREN:
        implicit_tag = IMPLICIT_CHILDREN[parent_tag]
        if not head:
            head = implicit_tag
        else:
            first = head.split()[0].split(".")[0].split("#")[0]
            if not first:
                # starts with . or # → prepend implicit tag instead of div
                head = implicit_tag + head
            elif first not in HTML_TAGS and "=" in first:
                head = implicit_tag + " " + head

    tag, classes, attrs = _parse_element_def(head)

    if tag == "style":
        rules = [_parse_style_item(child) for child in children]
        return StyleElement(classes=classes, attributes=attrs, rules=rules)

    if tag == "script":
        body = ""
        if children and children[0]["token"].type == "script_body":
            body = children[0]["token"].head
        return ScriptElement(classes=classes, attributes=attrs, body=body)

    text = token.text if token.text else None
    child_nodes = [_parse_node(child, tag) for child in children]
    return Element(
        tag=tag,
        classes=classes,
        attributes=attrs,
        text=text,
        children=child_nodes,
    )


# --- element definition parsing ---


def _split_respecting_parens(s: str) -> List[str]:
    parts: List[str] = []
    current: List[str] = []
    depth = 0
    for ch in s:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == " " and depth == 0:
            if current:
                parts.append("".join(current))
                current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    return parts


def _parse_element_def(
    head: str,
) -> Tuple[str, List[str], Dict[str, Union[str, bool]]]:
    parts = _split_respecting_parens(head)
    if not parts or not parts[0]:
        return "div", [], {}
    tag_part = parts[0]

    # implicit div: .foo or #bar
    if tag_part.startswith(".") or tag_part.startswith("#"):
        tag_part = "div" + tag_part

    # parse tag#id.class1.class2
    tag_id = None
    if "#" in tag_part:
        idx = tag_part.index("#")
        before = tag_part[:idx]
        after = tag_part[idx + 1 :]
        dot_idx = after.find(".")
        if dot_idx != -1:
            tag_id = after[:dot_idx]
            tag_part = before + after[dot_idx:]
        else:
            tag_id = after
            tag_part = before

    segments = tag_part.split(".")
    tag = segments[0] if segments[0] else "div"
    classes = [c for c in segments[1:] if c]

    attrs: Dict[str, Union[str, bool]] = {}
    if tag_id:
        attrs["id"] = tag_id
    for part in parts[1:]:
        if "=" in part:
            k, v = part.split("=", 1)
            attrs[k] = v
        else:
            attrs[part] = True

    return tag, classes, attrs


# --- style parsing ---


def _parse_style_item(item: dict) -> StyleRule:
    token: Token = item["token"]
    children: list = item["children"]

    if children:
        selector = token.head
        props = []
        child_rules = []
        for child in children:
            if child["children"]:
                child_rules.append(_parse_style_item(child))
            else:
                ct: Token = child["token"]
                if ct.has_colon:
                    props.append((ct.head, ct.text))
                else:
                    props.append((ct.head, ""))
        return StyleRule(
            selector=selector, properties=props, children=child_rules
        )
    else:
        if token.has_colon and not token.text:
            return StyleRule(selector=token.head, properties=[], children=[])
        elif token.has_colon:
            return StyleRule(
                selector="",
                properties=[(token.head, token.text)],
                children=[],
            )
        else:
            return StyleRule(
                selector="",
                properties=[(token.head, "")],
                children=[],
            )


# --- inline element detection ---


def parse_inline(text: str) -> Optional[Element]:
    if not text or ":" not in text:
        return None
    first_word = text.split()[0].split(".")[0]
    if first_word not in HTML_TAGS:
        return None

    from .lexer import find_colon

    colon_idx = find_colon(text)
    if colon_idx == -1:
        return None

    head = text[:colon_idx].rstrip()
    tail = text[colon_idx + 1 :].strip()

    tag, classes, attrs = _parse_element_def(head)
    return Element(
        tag=tag,
        classes=classes,
        attributes=attrs,
        text=tail if tail else None,
    )
