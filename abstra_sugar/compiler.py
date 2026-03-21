import re
from typing import List, Tuple

from .ast import Element, ForBlock, IfBlock, Node, ScriptElement, StyleElement, StyleRule
from .parser import parse_inline

VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}


_id_counter = 0


def _auto_id() -> str:
    global _id_counter
    _id_counter += 1
    return f"_s{_id_counter}"


def compile(nodes: List[Node]) -> str:
    global _id_counter
    _id_counter = 0
    lines: List[str] = []
    for node in nodes:
        _compile_node(node, 0, lines)
    return "\n".join(lines) + "\n"


def _compile_node(node: Node, depth: int, lines: List[str]) -> None:
    if isinstance(node, StyleElement):
        _compile_style(node, depth, lines)
    elif isinstance(node, ScriptElement):
        _compile_script(node, depth, lines)
    elif isinstance(node, (ForBlock, IfBlock)):
        # top-level dynamic block — wrap in a div
        wrapper = Element(tag="div", attributes={"id": _auto_id()}, children=[node])
        _compile_element(wrapper, depth, lines)
    else:
        _compile_element(node, depth, lines)


# --- HTML ---


def _has_dynamic(children: list) -> bool:
    return any(isinstance(c, (ForBlock, IfBlock)) for c in children)


def _compile_element(el: Element, depth: int, lines: List[str]) -> None:
    indent = "\t" * depth
    opening = _build_opening_tag(el.tag, el.classes, el.attributes)

    if el.tag in VOID_ELEMENTS:
        lines.append(f"{indent}{opening}")
        return

    if el.text:
        inline = parse_inline(el.text)
        if inline:
            inner = _compile_element_inline(inline)
            lines.append(f"{indent}{opening}{inner}</{el.tag}>")
        else:
            lines.append(f"{indent}{opening}{el.text}</{el.tag}>")
        return

    if not el.children:
        lines.append(f"{indent}{opening}</{el.tag}>")
        return

    # dynamic children → generate script
    if _has_dynamic(el.children):
        if "id" not in el.attributes:
            el.attributes["id"] = _auto_id()
        el_id = el.attributes["id"]
        opening = _build_opening_tag(el.tag, el.classes, el.attributes)
        lines.append(f"{indent}{opening}</{el.tag}>")
        lines.append(f"{indent}<script>")
        si = indent + "\t"
        lines.append(f"{si}(function() {{")
        lines.append(f"{si}\tlet _t = \"\";")
        for child in el.children:
            _compile_dynamic_child(child, si + "\t", lines)
        lines.append(
            f'{si}\tdocument.getElementById("{el_id}").innerHTML = _t;'
        )
        lines.append(f"{si}}})();")
        lines.append(f"{indent}</script>")
        return

    lines.append(f"{indent}{opening}")
    for child in el.children:
        _compile_node(child, depth + 1, lines)
    lines.append(f"{indent}</{el.tag}>")


def _compile_element_inline(el: Element) -> str:
    opening = _build_opening_tag(el.tag, el.classes, el.attributes)

    if el.tag in VOID_ELEMENTS:
        return opening

    result = opening

    if el.text:
        inline = parse_inline(el.text)
        if inline:
            result += _compile_element_inline(inline)
        else:
            result += el.text

    result += f"</{el.tag}>"
    return result


# --- Dynamic rendering (for/if in HTML) ---


def _interpolate(text: str) -> str:
    return re.sub(r"\{([^}]+)\}", r"${\1}", text)


def _compile_dynamic_child(child, indent: str, lines: List[str]) -> None:
    if isinstance(child, ForBlock):
        lines.append(
            f"{indent}for (let {child.var} {child.keyword} {child.iterable}) {{"
        )
        for sub in child.children:
            _compile_dynamic_child(sub, indent + "\t", lines)
        lines.append(f"{indent}}}")
    elif isinstance(child, IfBlock):
        lines.append(f"{indent}if ({child.condition}) {{")
        for sub in child.children:
            _compile_dynamic_child(sub, indent + "\t", lines)
        lines.append(f"{indent}}}")
    elif isinstance(child, Element):
        template = _compile_template_element(child)
        lines.append(f"{indent}_t += `{template}`;")


def _compile_template_element(el: Element) -> str:
    opening = _build_template_tag(el.tag, el.classes, el.attributes)

    if el.tag in VOID_ELEMENTS:
        return opening

    result = opening

    if el.text:
        inline = parse_inline(el.text)
        if inline:
            result += _compile_template_element(inline)
        else:
            result += _interpolate(el.text)
    else:
        for child in el.children:
            if isinstance(child, Element):
                result += _compile_template_element(child)

    result += f"</{el.tag}>"
    return result


def _build_template_tag(tag: str, classes: list, attrs: dict) -> str:
    parts = [f"<{tag}"]
    if classes:
        parts.append(f' class="{" ".join(classes)}"')
    for k, v in attrs.items():
        if v is True:
            parts.append(f" {k}")
        else:
            parts.append(f' {k}="{_interpolate(str(v))}"')
    parts.append(">")
    return "".join(parts)


def _build_opening_tag(tag: str, classes: list, attrs: dict) -> str:
    parts = [f"<{tag}"]
    if classes:
        parts.append(f' class="{" ".join(classes)}"')
    for k, v in attrs.items():
        if v is True:
            parts.append(f" {k}")
        else:
            parts.append(f' {k}="{v}"')
    parts.append(">")
    return "".join(parts)


# --- Style ---


def _compile_style(node: StyleElement, depth: int, lines: List[str]) -> None:
    indent = "\t" * depth
    opening = _build_opening_tag("style", node.classes, node.attributes)
    css = _compile_style_rules(node.rules, depth + 1)
    lines.append(f"{indent}{opening}")
    lines.extend(css)
    lines.append(f"{indent}</style>")


def _compile_style_rules(rules: List[StyleRule], depth: int) -> List[str]:
    lines: List[str] = []
    indent = "\t" * depth

    for rule in rules:
        if rule.selector and (rule.properties or rule.children):
            lines.append(f"{indent}{rule.selector} {{")
            inner = "\t" * (depth + 1)
            for p, v in rule.properties:
                lines.append(f"{inner}{p}: {v};")
            for child in rule.children:
                lines.extend(_compile_style_rules([child], depth + 1))
            lines.append(f"{indent}}}")
        elif rule.properties:
            for p, v in rule.properties:
                lines.append(f"{indent}{p}: {v};")

    return lines


# --- Script ---


def _compile_script(
    node: ScriptElement, depth: int, lines: List[str]
) -> None:
    indent = "\t" * depth
    opening = _build_opening_tag("script", node.classes, node.attributes)
    lines.append(f"{indent}{opening}")
    _compile_script_body(node.body, depth + 1, lines)
    lines.append(f"{indent}</script>")


def _parse_script_lines(body: str) -> List[Tuple[int, str, bool]]:
    parsed: List[Tuple[int, str, bool]] = []
    for line in body.split("\n"):
        if not line.strip():
            parsed.append((0, "", True))
            continue
        indent = 0
        for ch in line:
            if ch == "\t":
                indent += 1
            else:
                break
        parsed.append((indent, line.strip(), False))
    return parsed


def _compile_script_body(
    body: str, base_depth: int, out: List[str]
) -> None:
    parsed = _parse_script_lines(body)
    block_stack: List[Tuple[int, bool]] = []  # (indent, is_class)
    i = 0

    while i < len(parsed):
        indent, content, is_blank = parsed[i]

        if is_blank:
            out.append("")
            i += 1
            continue

        # collect trailing blanks so closing braces go before them
        trailing_blanks: List[str] = []
        while out and out[-1] == "":
            trailing_blanks.append(out.pop())

        # close blocks at >= current indent
        while block_stack and block_stack[-1][0] >= indent:
            closed_indent, _ = block_stack.pop()
            out.append("\t" * (base_depth + closed_indent) + "}")

        out.extend(trailing_blanks)

        prefix = "\t" * (base_depth + indent)
        in_class = bool(block_stack) and block_stack[-1][1]

        if content.endswith(":"):
            header = content[:-1].rstrip()
            is_class = header.startswith("class ")
            js_header = _compile_script_line(header, in_class)
            js_header = _compile_inline_arrows(js_header)

            if js_header == header and not is_class:
                # object literal — compile children inline
                obj_str, i = _compile_object_inline(parsed, i + 1, indent)
                if " = " in header:
                    lhs, rhs = header.split(" = ", 1)
                    stmt = f"{lhs} = {{{rhs}: {obj_str}}}"
                else:
                    stmt = f"{header}: {obj_str}"
                if _needs_semicolon(stmt):
                    stmt += ";"
                out.append(f"{prefix}{stmt}")
                continue

            out.append(f"{prefix}{js_header} {{")
            block_stack.append((indent, is_class))
        else:
            stmt = _compile_inline_arrows(content)
            if _needs_semicolon(stmt):
                stmt += ";"
            out.append(f"{prefix}{stmt}")

        i += 1

    # close remaining blocks
    trailing_blanks = []
    while out and out[-1] == "":
        trailing_blanks.append(out.pop())
    while block_stack:
        closed_indent, _ = block_stack.pop()
        out.append("\t" * (base_depth + closed_indent) + "}")


def _compile_object_inline(
    parsed: List[Tuple[int, str, bool]], start: int, parent_indent: int
) -> Tuple[str, int]:
    pairs: List[str] = []
    i = start

    while i < len(parsed):
        indent, content, is_blank = parsed[i]
        if is_blank:
            i += 1
            continue
        if indent <= parent_indent:
            break

        if content.endswith(":"):
            key = content[:-1].rstrip()
            sub_obj, i = _compile_object_inline(parsed, i + 1, indent)
            pairs.append(f"{key}: {sub_obj}")
        else:
            pairs.append(content)
            i += 1

    return "{" + ", ".join(pairs) + "}", i


def _compile_inline_arrows(stmt: str) -> str:
    return re.sub(r"\(([^)]*)\):", r"(\1) =>", stmt)


def _needs_semicolon(stmt: str) -> bool:
    if stmt.endswith(";") or stmt.endswith("{") or stmt.endswith("("):
        return False
    if stmt.startswith("//"):
        return False
    return True


def _compile_script_line(line: str, in_class: bool) -> str:
    m = re.match(r"for\s+(.+?)\s+(of|in)\s+(.+)", line)
    if m:
        var, keyword, expr = m.groups()
        return f"for (let {var} {keyword} {expr})"

    m = re.match(r"else\s+if\s+(.+)", line)
    if m:
        return f"else if ({m.group(1)})"

    if line == "else":
        return "else"

    m = re.match(r"if\s+(.+)", line)
    if m:
        return f"if ({m.group(1)})"

    m = re.match(r"while\s+(.+)", line)
    if m:
        return f"while ({m.group(1)})"

    m = re.match(r"class\s+(\w+(?:\s+extends\s+\w+)?)", line)
    if m:
        return f"class {m.group(1)}"

    # try / catch / finally
    if line == "try":
        return "try"
    m = re.match(r"catch\s*\(([^)]*)\)$", line)
    if m:
        return f"catch({m.group(1)})"
    if line == "finally":
        return "finally"

    # arrow function: (params)
    m = re.match(r"\(([^)]*)\)$", line)
    if m:
        return f"({m.group(1)}) =>"

    # named function / method
    m = re.match(r"(async\s+)?(\w+)\s*\(([^)]*)\)$", line)
    if m:
        async_prefix = m.group(1) or ""
        name = m.group(2)
        args = m.group(3)
        if in_class or name == "constructor":
            return f"{async_prefix}{name}({args})"
        else:
            return f"{async_prefix}function {name}({args})"

    # trailing arrow: expr(... , (params)) → expr(... , (params) =>)
    if line.endswith(")"):
        depth = 0
        for i in range(len(line) - 1, -1, -1):
            if line[i] == ")":
                depth += 1
            elif line[i] == "(":
                depth -= 1
                if depth == 0:
                    return line[:i] + "(" + line[i + 1 : -1] + ") =>"

    return line
