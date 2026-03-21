import re
from types import SimpleNamespace
from typing import Any, List, Optional, Tuple

from .ast import (
    ComponentCall, ComponentDef, Element, ForBlock, IfBlock, Node,
    ScriptElement, StyleElement, StyleRule,
)
from .parser import parse_inline

VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
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
    "len": len, "str": str, "int": int, "float": float, "bool": bool,
    "list": list, "dict": dict, "tuple": tuple, "set": set,
    "range": range, "enumerate": enumerate, "zip": zip, "map": map,
    "filter": filter, "sorted": sorted, "reversed": reversed,
    "min": min, "max": max, "sum": sum, "abs": abs, "round": round,
    "isinstance": isinstance, "hasattr": hasattr, "getattr": getattr,
    "True": True, "False": False, "None": None,
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
    node: Node, depth: int, lines: List[str], data: Optional[dict],
    components: Optional[dict] = None, slot: Optional[list] = None,
) -> None:
    comps = components or {}
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
    else:
        _compile_element(node, depth, lines, data, comps, slot)


# --- HTML ---


def _compile_element(
    el: Element, depth: int, lines: List[str], data: Optional[dict],
    components: Optional[dict] = None, slot: Optional[list] = None,
) -> None:
    # slot replacement
    if el.tag == "slot" and slot:
        for s in slot:
            _compile_node(s, depth, lines, data, components)
        return

    indent = "\t" * depth
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
    block: ForBlock, depth: int, lines: List[str], data: Optional[dict],
    components: Optional[dict] = None, slot: Optional[list] = None,
) -> None:
    if data is None:
        return
    iterable = _eval_expr(block.iterable, data)
    for item in iterable:
        child_data = {**data, block.var: _wrap(item)}
        for child in block.children:
            _compile_node(child, depth, lines, child_data, components, slot)


def _compile_if_block(
    block: IfBlock, depth: int, lines: List[str], data: Optional[dict],
    components: Optional[dict] = None, slot: Optional[list] = None,
) -> None:
    if data is None:
        return
    if _eval_expr(block.condition, data):
        for child in block.children:
            _compile_node(child, depth, lines, data, components, slot)


# --- Components ---


def _compile_component_call(
    call: ComponentCall, depth: int, lines: List[str],
    data: Optional[dict], components: dict,
) -> None:
    comp = components.get(call.name)
    if comp is None:
        return

    # bind args to params
    args = [a.strip() for a in call.args_raw.split(",") if a.strip()] if call.args_raw else []
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
    indent = "\t" * depth
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
    indent = "\t" * depth
    mx = mixins or {}

    for rule in rules:
        # skip mixin definitions
        if re.match(r"\w+\s*=\s*\([^)]*\)$", rule.selector):
            continue

        if rule.selector and (rule.properties or rule.children):
            lines.append(f"{indent}{rule.selector} {{")
            inner = "\t" * (depth + 1)
            for p, v in rule.properties:
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
                mm = re.match(r"@(\w+)\(([^)]*)\)$", p)
                if mm and mm.group(1) in mx:
                    mixin = mx[mm.group(1)]
                    for mp, mv in mixin.properties:
                        lines.append(f"{indent}{mp}: {mv};")
                else:
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


def _compile_template_block(
    lines: List[Tuple[int, str, bool]], base_indent: int, tmpl_type: str
) -> str:
    # rebuild sugar source from parsed lines
    src_lines: List[str] = []
    for ind, content, is_blank in lines:
        if is_blank:
            continue
        src_lines.append("\t" * (ind - base_indent) + content)
    src = "\n".join(src_lines)

    if tmpl_type == "html!":
        from .lexer import scan
        from .parser import parse as parse_nodes

        nodes = parse_nodes(scan(src))
        html = compile(nodes, data=None)
        html = html.rstrip("\n")
        # {expr} → ${expr} for template literal
        html = re.sub(r"\{([^}]+)\}", r"${\1}", html)
        # collapse to single line
        html = re.sub(r"\n\t*", "", html)
        return html

    # css! and js! — pass through as raw text for now
    return src.replace("\n", "\\n")


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

        trailing_blanks: List[str] = []
        while out and out[-1] == "":
            trailing_blanks.append(out.pop())

        while block_stack and block_stack[-1][0] >= indent:
            closed_indent, _ = block_stack.pop()
            out.append("\t" * (base_depth + closed_indent) + "}")

        out.extend(trailing_blanks)

        prefix = "\t" * (base_depth + indent)
        in_class = bool(block_stack) and block_stack[-1][1]

        # html!/css!/js! template literals
        tmpl_match = re.match(r"(.+?)(html!|css!|js!)\s*:$", content)
        if tmpl_match:
            tmpl_prefix = tmpl_match.group(1)
            tmpl_type = tmpl_match.group(2)
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
            stmt = f"{tmpl_prefix}`{tmpl_html}`"
            if _needs_semicolon(stmt):
                stmt += ";"
            out.append(f"{prefix}{stmt}")
            i = j
            continue

        if content.endswith(":"):
            header = content[:-1].rstrip()
            is_class = header.startswith("class ")
            js_header = _compile_script_line(header, in_class)
            js_header = _compile_inline_arrows(js_header)

            if js_header == header and not is_class:
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
