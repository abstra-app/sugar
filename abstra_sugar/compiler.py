import re
from types import SimpleNamespace
from typing import Any, List, Optional, Tuple

from .ast import (
    Comment,
    ComponentCall,
    ComponentDef,
    Element,
    ForBlock,
    IfBlock,
    MarkdownLiteral,
    MathLiteral,
    Node,
    ScriptElement,
    StyleElement,
    StyleRule,
    SvgLiteral,
    TableLiteral,
)
from .parser import parse_inline

VOID_ELEMENTS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


# --- Data helpers for templating ---


def _wrap(val: Any) -> Any:
    if isinstance(val, dict):
        return SimpleNamespace(**{k: _wrap(v) for k, v in val.items()})
    if isinstance(val, list):
        return [_wrap(v) for v in val]
    return val


def _wrap_data(data: dict) -> dict:
    return {k: _wrap(v) for k, v in data.items()}


_SAFE_BUILTINS = {
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "set": set,
    "range": range,
    "enumerate": enumerate,
    "zip": zip,
    "map": map,
    "filter": filter,
    "sorted": sorted,
    "reversed": reversed,
    "min": min,
    "max": max,
    "sum": sum,
    "abs": abs,
    "round": round,
    "isinstance": isinstance,
    "hasattr": hasattr,
    "getattr": getattr,
    "True": True,
    "False": False,
    "None": None,
}


def _eval_expr(expr: str, data: dict) -> Any:
    return eval(expr, {"__builtins__": _SAFE_BUILTINS}, data)


def _interpolate(text: str, data: dict) -> str:
    def replace(m: re.Match) -> str:
        return str(_eval_expr(m.group(1), data))

    return re.sub(r"\{([^}]+)\}", replace, text)


# --- Main entry ---


def compile(nodes: List[Node], data: Optional[dict] = None) -> str:
    ctx = _wrap_data(data) if data is not None else None
    components: dict = {}
    _collect_components(nodes, components)
    lines: List[str] = []
    for node in nodes:
        if isinstance(node, ComponentDef):
            continue
        _compile_node(node, 0, lines, ctx, components)
    return "\n".join(lines) + "\n"


def _collect_components(nodes: list, components: dict) -> None:
    for node in nodes:
        if isinstance(node, ComponentDef):
            components[node.name] = node
        elif isinstance(node, Element):
            _collect_components(node.children, components)


def _compile_node(
    node: Node,
    depth: int,
    lines: List[str],
    data: Optional[dict],
    components: Optional[dict] = None,
    slot: Optional[list] = None,
) -> None:
    comps = components or {}
    if isinstance(node, Comment):
        indent = " " * depth
        lines.append(f"{indent}<!--{node.text} -->")
        return
    if isinstance(node, StyleElement):
        _compile_style(node, depth, lines)
    elif isinstance(node, ScriptElement):
        _compile_script(node, depth, lines)
    elif isinstance(node, ForBlock):
        _compile_for_block(node, depth, lines, data, comps, slot)
    elif isinstance(node, IfBlock):
        _compile_if_block(node, depth, lines, data, comps, slot)
    elif isinstance(node, ComponentDef):
        pass
    elif isinstance(node, ComponentCall):
        _compile_component_call(node, depth, lines, data, comps)
    elif isinstance(node, TableLiteral):
        _compile_table_html(node, depth, lines, data)
    elif isinstance(node, MarkdownLiteral):
        _compile_markdown_html(node, depth, lines, data)
    elif isinstance(node, MathLiteral):
        _compile_math_html(node, depth, lines)
    elif isinstance(node, SvgLiteral):
        _compile_svg_html(node, depth, lines, data)
    else:
        _compile_element(node, depth, lines, data, comps, slot)


# --- table!: in HTML ---


def _compile_table_html(
    table: TableLiteral,
    depth: int,
    lines: List[str],
    data: Optional[dict] = None,
) -> None:
    indent = " " * depth
    opening = _build_opening_tag("table", table.classes, table.attributes, data)
    lines.append(f"{indent}{opening}")
    d1 = " " * (depth + 1)
    d2 = " " * (depth + 2)
    d3 = " " * (depth + 3)
    # thead
    lines.append(f"{d1}<thead>")
    lines.append(f"{d2}<tr>")
    for h in table.headers:
        val = _interpolate(h, data) if data is not None else h
        lines.append(f"{d3}<th>{val}</th>")
    lines.append(f"{d2}</tr>")
    lines.append(f"{d1}</thead>")
    # tbody
    lines.append(f"{d1}<tbody>")
    for row in table.rows:
        lines.append(f"{d2}<tr>")
        for cell in row:
            val = _interpolate(cell, data) if data is not None else cell
            lines.append(f"{d3}<td>{val}</td>")
        lines.append(f"{d2}</tr>")
    lines.append(f"{d1}</tbody>")
    lines.append(f"{indent}</table>")


def _compile_math_html(
    node: MathLiteral,
    depth: int,
    lines: List[str],
) -> None:
    import latex2mathml.converter as _l2m

    indent = " " * depth
    mathml = _l2m.convert(node.source)
    lines.append(f"{indent}{mathml}")


_SVG_SHAPE_RE = re.compile(r"^(circle|rect|ellipse|line|polyline|polygon|path|text)\s+")


def _compile_svg_html(
    node: SvgLiteral,
    depth: int,
    lines: List[str],
    data: Optional[dict] = None,
) -> None:
    indent = " " * depth
    opening = _build_opening_tag("svg", node.classes, node.attributes, data)
    lines.append(f"{indent}{opening}")
    d1 = " " * (depth + 1)
    src_lines = node.source.split("\n")
    i = 0
    while i < len(src_lines):
        line = src_lines[i].strip()
        if not line:
            i += 1
            continue

        # path with block body: "path attrs:" followed by indented commands
        path_match = re.match(r"^path\b(.*):$", line)
        if path_match:
            attr_str = path_match.group(1).strip()
            # collect indented path commands
            base_indent = len(src_lines[i]) - len(src_lines[i].lstrip())
            cmds: List[str] = []
            i += 1
            while i < len(src_lines):
                cl = src_lines[i]
                cl_stripped = cl.strip()
                if not cl_stripped:
                    i += 1
                    continue
                cl_indent = len(cl) - len(cl.lstrip())
                if cl_indent <= base_indent:
                    break
                cmds.append(_svg_path_cmd(cl_stripped))
                i += 1
            d_attr = " ".join(cmds).strip()
            attrs = [f'd="{d_attr}"']
            for p in attr_str.split():
                if "=" in p:
                    k, v = p.split("=", 1)
                    attrs.append(f'{k}="{v}"')
            lines.append(f"{d1}<path {' '.join(attrs)}/>")
            continue

        m = _SVG_SHAPE_RE.match(line)
        if m:
            tag = m.group(1)
            rest = line[m.end() :]
            lines.append(f"{d1}{_svg_shape(tag, rest)}")
        else:
            lines.append(f"{d1}{line}")
        i += 1
    lines.append(f"{indent}</svg>")


def _svg_path_cmd(line: str) -> str:
    """Pass through SVG path data as-is (M, L, C, Z, etc.)."""
    return line


def _svg_shape(tag: str, rest: str) -> str:
    """Parse simplified SVG shape syntax into an SVG element."""
    attrs: List[str] = []
    text_content = ""

    # positional args depend on shape type
    parts = rest.split()
    positional: List[str] = []
    named: List[str] = []
    for p in parts:
        if "=" in p:
            named.append(p)
        else:
            positional.append(p)

    if tag == "circle" and len(positional) >= 2:
        attrs.append(f'cx="{positional[0]}"')
        attrs.append(f'cy="{positional[1]}"')
        positional = positional[2:]
    elif tag == "rect" and len(positional) >= 2:
        attrs.append(f'x="{positional[0]}"')
        attrs.append(f'y="{positional[1]}"')
        # check WxH
        if positional[2:] and "x" in positional[2]:
            w, h = positional[2].split("x", 1)
            attrs.append(f'width="{w}"')
            attrs.append(f'height="{h}"')
            positional = positional[3:]
        else:
            positional = positional[2:]
    elif tag == "ellipse" and len(positional) >= 2:
        attrs.append(f'cx="{positional[0]}"')
        attrs.append(f'cy="{positional[1]}"')
        positional = positional[2:]
    elif tag == "line" and len(positional) >= 4:
        attrs.append(f'x1="{positional[0]}"')
        attrs.append(f'y1="{positional[1]}"')
        attrs.append(f'x2="{positional[2]}"')
        attrs.append(f'y2="{positional[3]}"')
        positional = positional[4:]
    elif tag == "text" and len(positional) >= 2:
        attrs.append(f'x="{positional[0]}"')
        attrs.append(f'y="{positional[1]}"')
        # remaining positional is text content
        text_content = " ".join(positional[2:])
        positional = []

    # remaining named attrs
    for p in named:
        k, v = p.split("=", 1)
        attrs.append(f'{k}="{v}"')

    attr_str = " ".join(attrs)
    if text_content:
        return f"<{tag} {attr_str}>{text_content}</{tag}>"
    if tag == "text":
        return f"<{tag} {attr_str}></{tag}>"
    return f"<{tag} {attr_str}/>"


def _compile_markdown_html(
    node: MarkdownLiteral,
    depth: int,
    lines: List[str],
    data: Optional[dict] = None,
) -> None:
    import markdown as _md

    indent = " " * depth
    html = _md.markdown(node.source)
    if data is not None:
        html = _interpolate(html, data)
    opening = _build_opening_tag("div", node.classes, node.attributes, data)
    lines.append(f"{indent}{opening}")
    for h_line in html.split("\n"):
        if h_line.strip():
            lines.append(f"{indent}\t{h_line}")
    lines.append(f"{indent}</div>")


# --- HTML ---


def _compile_element(
    el: Element,
    depth: int,
    lines: List[str],
    data: Optional[dict],
    components: Optional[dict] = None,
    slot: Optional[list] = None,
) -> None:
    # slot replacement
    if el.tag == "slot" and slot:
        for s in slot:
            _compile_node(s, depth, lines, data, components)
        return

    indent = " " * depth
    opening = _build_opening_tag(el.tag, el.classes, el.attributes, data)

    if el.tag in VOID_ELEMENTS:
        lines.append(f"{indent}{opening}")
        return

    if el.text:
        text = _interpolate(el.text, data) if data is not None else el.text
        inline = parse_inline(el.text)
        if inline:
            inner = _compile_element_inline(inline, data)
            lines.append(f"{indent}{opening}{inner}</{el.tag}>")
        else:
            lines.append(f"{indent}{opening}{text}</{el.tag}>")
        return

    if not el.children:
        lines.append(f"{indent}{opening}</{el.tag}>")
        return

    lines.append(f"{indent}{opening}")
    for child in el.children:
        _compile_node(child, depth + 1, lines, data, components, slot)
    lines.append(f"{indent}</{el.tag}>")


def _compile_element_inline(el: Element, data: Optional[dict]) -> str:
    opening = _build_opening_tag(el.tag, el.classes, el.attributes, data)

    if el.tag in VOID_ELEMENTS:
        return opening

    result = opening

    if el.text:
        inline = parse_inline(el.text)
        if inline:
            result += _compile_element_inline(inline, data)
        else:
            result += _interpolate(el.text, data) if data is not None else el.text

    result += f"</{el.tag}>"
    return result


# --- Templating (for/if in HTML) ---


def _compile_for_block(
    block: ForBlock,
    depth: int,
    lines: List[str],
    data: Optional[dict],
    components: Optional[dict] = None,
    slot: Optional[list] = None,
) -> None:
    if data is None:
        return
    iterable = _eval_expr(block.iterable, data)
    for item in iterable:
        child_data = {**data, block.var: _wrap(item)}
        for child in block.children:
            _compile_node(child, depth, lines, child_data, components, slot)


def _compile_if_block(
    block: IfBlock,
    depth: int,
    lines: List[str],
    data: Optional[dict],
    components: Optional[dict] = None,
    slot: Optional[list] = None,
) -> None:
    if data is None:
        return
    if _eval_expr(block.condition, data):
        for child in block.children:
            _compile_node(child, depth, lines, data, components, slot)


# --- Components ---


def _compile_component_call(
    call: ComponentCall,
    depth: int,
    lines: List[str],
    data: Optional[dict],
    components: dict,
) -> None:
    comp = components.get(call.name)
    if comp is None:
        return

    # bind args to params
    args = (
        [a.strip() for a in call.args_raw.split(",") if a.strip()]
        if call.args_raw
        else []
    )
    call_data = dict(data) if data else {}
    for param, arg in zip(comp.params, args):
        try:
            call_data[param] = _eval_expr(arg, call_data)
        except Exception:
            call_data[param] = arg

    call_data_ctx = call_data if call_data else data

    for child in comp.children:
        _compile_node(child, depth, lines, call_data_ctx, components, call.children)


# --- Opening tags ---


def _build_opening_tag(
    tag: str, classes: list, attrs: dict, data: Optional[dict] = None
) -> str:
    parts = [f"<{tag}"]
    if classes:
        parts.append(f' class="{" ".join(classes)}"')
    for k, v in attrs.items():
        if v is True:
            parts.append(f" {k}")
        else:
            val = _interpolate(str(v), data) if data is not None else str(v)
            parts.append(f' {k}="{val}"')
    parts.append(">")
    return "".join(parts)


# --- Style ---


def _compile_style(node: StyleElement, depth: int, lines: List[str]) -> None:
    indent = " " * depth
    opening = _build_opening_tag("style", node.classes, node.attributes)

    # collect CSS mixins
    mixins: dict = {}
    for rule in node.rules:
        m = re.match(r"(\w+)\s*=\s*\(([^)]*)\)$", rule.selector)
        if m:
            mixins[m.group(1)] = rule

    css = _compile_style_rules(node.rules, depth + 1, mixins)
    lines.append(f"{indent}{opening}")
    lines.extend(css)
    lines.append(f"{indent}</style>")


def _compile_style_rules(
    rules: List[StyleRule], depth: int, mixins: Optional[dict] = None
) -> List[str]:
    lines: List[str] = []
    indent = " " * depth
    mx = mixins or {}

    for rule in rules:
        # skip mixin definitions
        if re.match(r"\w+\s*=\s*\([^)]*\)$", rule.selector):
            continue

        if rule.selector and (rule.properties or rule.children):
            lines.append(f"{indent}{rule.selector} {{")
            inner = " " * (depth + 1)
            for p, v in rule.properties:
                # CSS comment
                if p == "/*":
                    lines.append(f"{inner}{p}{v}")
                    continue
                # expand mixin calls: @name()
                mm = re.match(r"@(\w+)\(([^)]*)\)$", p)
                if mm and mm.group(1) in mx:
                    mixin = mx[mm.group(1)]
                    for mp, mv in mixin.properties:
                        lines.append(f"{inner}{mp}: {mv};")
                else:
                    lines.append(f"{inner}{p}: {v};")
            for child in rule.children:
                lines.extend(_compile_style_rules([child], depth + 1, mx))
            lines.append(f"{indent}}}")
        elif rule.properties:
            for p, v in rule.properties:
                if p == "/*":
                    lines.append(f"{indent}{p}{v}")
                    continue
                mm = re.match(r"@(\w+)\(([^)]*)\)$", p)
                if mm and mm.group(1) in mx:
                    mixin = mx[mm.group(1)]
                    for mp, mv in mixin.properties:
                        lines.append(f"{indent}{mp}: {mv};")
                else:
                    lines.append(f"{indent}{p}: {v};")

    return lines


# --- Script ---


def _compile_script(node: ScriptElement, depth: int, lines: List[str]) -> None:
    indent = " " * depth
    opening = _build_opening_tag("script", node.classes, node.attributes)
    lines.append(f"{indent}{opening}")
    _compile_script_body(node.body, depth + 1, lines)
    lines.append(f"{indent}</script>")


def _compile_template_block(
    lines: List[Tuple[int, str, bool]], base_indent: int, tmpl_type: str
) -> str:
    # rebuild sugar source from parsed lines
    src_lines: List[str] = []
    for ind, content, is_blank in lines:
        if is_blank:
            continue
        src_lines.append(" " * (ind - base_indent) + content)
    src = "\n".join(src_lines)

    if tmpl_type in ("html!", "htm!"):
        from .lexer import scan
        from .parser import parse as parse_nodes

        nodes = parse_nodes(scan(src))
        html = compile(nodes, data=None)
        html = html.rstrip("\n")
        # {expr} → ${expr} for template literal (skip already-prefixed ${…})
        html = re.sub(r"(?<!\$)\{([^}]+)\}", r"${\1}", html)
        if tmpl_type == "htm!":
            # unquote "${…}" in attributes so HTM receives JS values
            html = re.sub(r'="(\$\{[^}]+\})"', r"=\1", html)
        # collapse to single line
        html = re.sub(r"\n\t*", "", html)
        return html

    if tmpl_type == "text!":
        # raw text lines joined with \n, {expr} → ${expr}
        text = "\\n".join(src_lines)
        text = re.sub(r"\{([^}]+)\}", r"${\1}", text)
        return text

    if tmpl_type == "table!":
        return _compile_table_literal(src_lines)

    # css! and js! — pass through as raw text for now
    return src.replace("\n", "\\n")


def _compile_table_literal(src_lines: List[str]) -> str:
    """Compile table!: block into a JS array of objects.

    First line = header (column names separated by |).
    Subsequent lines = rows (values separated by |).
    """
    if not src_lines:
        return "[]"
    headers = [h.strip() for h in src_lines[0].split("|")]
    rows: List[str] = []
    for line in src_lines[1:]:
        values = [v.strip() for v in line.split("|")]
        pairs = []
        for key, val in zip(headers, values):
            if key and val:
                pairs.append(f"{key}: {val}")
        rows.append("{" + ", ".join(pairs) + "}")
    return "[" + ", ".join(rows) + "]"


def _parse_script_lines(body: str) -> List[Tuple[int, str, bool]]:
    parsed: List[Tuple[int, str, bool]] = []
    for line in body.split("\n"):
        if not line.strip():
            parsed.append((0, "", True))
            continue
        indent = 0
        for ch in line:
            if ch == " ":
                indent += 1
            else:
                break
        parsed.append((indent, line.strip(), False))
    return parsed


def _compile_script_body(body: str, base_depth: int, out: List[str]) -> None:
    parsed = _parse_script_lines(body)
    block_stack: List[Tuple[int, bool]] = []  # (indent, is_class)
    i = 0

    while i < len(parsed):
        indent, content, is_blank = parsed[i]

        if is_blank:
            out.append("")
            i += 1
            continue

        trailing_blanks: List[str] = []
        while out and out[-1] == "":
            trailing_blanks.append(out.pop())

        while block_stack and block_stack[-1][0] >= indent:
            closed_indent, _ = block_stack.pop()
            out.append(" " * (base_depth + closed_indent) + "}")

        out.extend(trailing_blanks)

        prefix = " " * (base_depth + indent)
        in_class = bool(block_stack) and block_stack[-1][1]

        # html!/htm!/css!/js!/text!/table! template literals
        tmpl_match = re.match(
            r"(.*?)(html!|htm!|css!|js!|text!|table!)\s*:\s*(.+)$", content
        )
        tmpl_block_match = (
            re.match(r"(.*?)(html!|htm!|css!|js!|text!|table!)\s*:$", content)
            if not tmpl_match
            else None
        )
        if tmpl_match or tmpl_block_match:
            m = tmpl_match or tmpl_block_match
            assert m is not None
            tmpl_prefix = m.group(1)
            tmpl_type = m.group(2)
            if tmpl_match:
                # inline form: htm!: {App}
                inline_content = tmpl_match.group(3)
                tmpl_html = re.sub(r"(?<!\$)\{([^}]+)\}", r"${\1}", inline_content)
                j = i + 1
            else:
                # block form: htm!:\n  children
                tmpl_lines: List[Tuple[int, str, bool]] = []
                j = i + 1
                while j < len(parsed):
                    ci, cc, cb = parsed[j]
                    if not cb and ci <= indent:
                        break
                    tmpl_lines.append(parsed[j])
                    j += 1
                tmpl_html = _compile_template_block(
                    tmpl_lines, indent + 1, tmpl_type
                )
            if tmpl_type == "table!":
                stmt = f"{tmpl_prefix}{tmpl_html}"
            elif tmpl_type == "htm!":
                stmt = f"{tmpl_prefix}html`{tmpl_html}`"
            else:
                stmt = f"{tmpl_prefix}`{tmpl_html}`"
            if _needs_semicolon(stmt):
                stmt += ";"
            out.append(f"{prefix}{stmt}")
            i = j
            continue

        # skip processing for JS comments
        if content.startswith("//"):
            out.append(f"{prefix}{content}")
            i += 1
            continue

        if content.endswith(":"):
            header = content[:-1].rstrip()
            is_class = header.startswith("class ")
            js_header = _compile_script_line(header, in_class)
            js_header = _compile_inline_arrows(js_header)

            _BLOCK_KEYWORDS = {"else", "try", "finally"}
            _is_method = in_class and re.match(r"\w+\s*\(", header)
            if (
                js_header == header
                and not is_class
                and header not in _BLOCK_KEYWORDS
                and not _is_method
            ):
                obj_str, i = _compile_collection_inline(parsed, i + 1, indent)
                eq_match = re.match(r"(.+?)\s*=\s*(.*)", header)
                if eq_match:
                    lhs, rhs = eq_match.group(1), eq_match.group(2)
                    if rhs:
                        stmt = f"{lhs} = {{{rhs}: {obj_str}}}"
                    else:
                        stmt = f"{lhs} = {obj_str}"
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
            stmt = _compile_list_comprehension(stmt)
            if _needs_semicolon(stmt):
                stmt += ";"
            out.append(f"{prefix}{stmt}")

        i += 1

    trailing_blanks = []
    while out and out[-1] == "":
        trailing_blanks.append(out.pop())
    while block_stack:
        closed_indent, _ = block_stack.pop()
        out.append(" " * (base_depth + closed_indent) + "}")


def _compile_collection_inline(
    parsed: List[Tuple[int, str, bool]], start: int, parent_indent: int
) -> Tuple[str, int]:
    """Compile indented block into either {object} or [array].

    Standalone ``:`` → opens an object item inside an array.
    ``key: value`` or ending with ``:`` → object property.
    Bare values (no colon) → array elements.
    """
    pairs: List[str] = []
    has_keys = False
    has_item_separators = False
    i = start

    while i < len(parsed):
        indent, content, is_blank = parsed[i]
        if is_blank:
            i += 1
            continue
        if indent <= parent_indent:
            break

        # standalone ":" → object item separator in array
        if content == ":":
            has_item_separators = True
            obj, i = _compile_collection_inline(parsed, i + 1, indent)
            pairs.append(obj)
            continue

        if content.endswith(":"):
            has_keys = True
            key = content[:-1].rstrip()
            sub, i = _compile_collection_inline(parsed, i + 1, indent)
            pairs.append(f"{key}: {sub}")
        else:
            # detect key: value (colon preceded by word, followed by space)
            if re.match(r'[\w"\']+\s*:', content):
                has_keys = True
            pairs.append(content)
            i += 1

    if has_item_separators:
        return "[" + ", ".join(pairs) + "]", i
    if has_keys:
        return "{" + ", ".join(pairs) + "}", i
    return "[" + ", ".join(pairs) + "]", i


def _compile_inline_arrows(stmt: str) -> str:
    return re.sub(r"\(([^)]*)\):", r"(\1) =>", stmt)


# [expr for var of iterable if condition]
_COMPREHENSION_RE = re.compile(
    r"\[(.+?)\s+for\s+(\w+)\s+of\s+(.+?)"
    r"(?:\s+if\s+(.+?))?\]"
)


def _compile_list_comprehension(stmt: str) -> str:
    def _replace(m: re.Match) -> str:
        expr, var, iterable, condition = m.groups()
        if condition:
            return f"{iterable}.filter(({var}) => {condition}).map(({var}) => {expr})"
        return f"{iterable}.map(({var}) => {expr})"

    return _COMPREHENSION_RE.sub(_replace, stmt)


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

    if line == "try":
        return "try"
    m = re.match(r"catch\s*\(([^)]*)\)$", line)
    if m:
        return f"catch({m.group(1)})"
    if line == "finally":
        return "finally"

    m = re.match(r"\(([^)]*)\)$", line)
    if m:
        return f"({m.group(1)}) =>"

    m = re.match(r"(async\s+)?(\w+)\s*\(([^)]*)\)$", line)
    if m:
        async_prefix = m.group(1) or ""
        name = m.group(2)
        args = m.group(3)
        if in_class or name == "constructor":
            return f"{async_prefix}{name}({args})"
        else:
            return f"{async_prefix}function {name}({args})"

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
