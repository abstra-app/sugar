"""Parser that converts raw Sugar-JS script body strings into ScriptNode ASTs."""

import re
from typing import List, Tuple

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
    ScriptNode,
    ScriptStatement,
    ScriptTemplateLiteral,
    ScriptTry,
    ScriptWhileLoop,
)


def parse_script(body: str) -> List[ScriptNode]:
    """Parse a raw script body string into a list of ScriptNode AST nodes."""
    parsed = _parse_lines(body)
    nodes, _ = _parse_block(parsed, 0, -1)
    return nodes


def _parse_lines(body: str) -> List[Tuple[int, str, bool]]:
    """Parse body into (indent, content, is_blank) tuples."""
    result: List[Tuple[int, str, bool]] = []
    for line in body.split("\n"):
        if not line.strip():
            result.append((0, "", True))
            continue
        indent = 0
        for ch in line:
            if ch == " ":
                indent += 1
            else:
                break
        result.append((indent, line.strip(), False))
    return result


def _collect_children(
    parsed: List[Tuple[int, str, bool]], start: int, parent_indent: int
) -> Tuple[List[Tuple[int, str, bool]], int]:
    """Collect all lines that are children of a block header at parent_indent."""
    children: List[Tuple[int, str, bool]] = []
    i = start
    while i < len(parsed):
        indent, _, is_blank = parsed[i]
        if is_blank:
            children.append(parsed[i])
            i += 1
            continue
        if indent <= parent_indent:
            break
        children.append(parsed[i])
        i += 1
    return children, i


def _parse_block(
    parsed: List[Tuple[int, str, bool]], start: int, parent_indent: int
) -> Tuple[List[ScriptNode], int]:
    """Parse a sequence of lines at the same block level into ScriptNodes."""
    nodes: List[ScriptNode] = []
    i = start

    while i < len(parsed):
        indent, content, is_blank = parsed[i]

        if is_blank:
            i += 1
            continue

        if parent_indent >= 0 and indent <= parent_indent:
            break

        # --- Template literals (check before block-ending-colon) ---
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
                inline_content = tmpl_match.group(3)
                tmpl_content = _compile_template_inline(inline_content, tmpl_type)
                j = i + 1
            else:
                tmpl_lines: List[Tuple[int, str, bool]] = []
                j = i + 1
                while j < len(parsed):
                    ci, _, cb = parsed[j]
                    if not cb and ci <= indent:
                        break
                    tmpl_lines.append(parsed[j])
                    j += 1
                tmpl_content = _compile_template_block(
                    tmpl_lines, indent + 1, tmpl_type
                )
            nodes.append(
                ScriptTemplateLiteral(
                    prefix=tmpl_prefix,
                    literal_type=tmpl_type,
                    content=tmpl_content,
                )
            )
            i = j
            continue

        # --- Comments ---
        if content.startswith("//"):
            comment_text = content[2:].strip()
            nodes.append(ScriptComment(text=comment_text))
            i += 1
            continue

        # --- Block headers (lines ending with :) ---
        if content.endswith(":"):
            header = content[:-1].rstrip()

            # Collect child lines
            child_lines, next_i = _collect_children(parsed, i + 1, indent)

            # Class
            cls_match = re.match(
                r"class\s+(\w+)(?:\s+extends\s+(\w+))?$", header
            )
            if cls_match:
                name = cls_match.group(1)
                extends = cls_match.group(2)
                methods, _ = _parse_block(child_lines, 0, indent)
                nodes.append(ScriptClass(name=name, extends=extends, methods=methods))
                i = next_i
                continue

            # For loop (check before function to avoid matching `for` as func name)
            for_match = re.match(r"for\s+(.+?)\s+(of|in)\s+(.+)$", header)
            if for_match:
                var = for_match.group(1)
                keyword = for_match.group(2)
                iterable = for_match.group(3)
                body, _ = _parse_block(child_lines, 0, indent)
                nodes.append(
                    ScriptForLoop(
                        var=var, keyword=keyword, iterable=iterable, body=body
                    )
                )
                i = next_i
                continue

            # While loop
            while_match = re.match(r"while\s+(.+)$", header)
            if while_match:
                condition = while_match.group(1)
                body, _ = _parse_block(child_lines, 0, indent)
                nodes.append(ScriptWhileLoop(condition=condition, body=body))
                i = next_i
                continue

            # If
            if_match = re.match(r"if\s+(.+)$", header)
            if if_match:
                condition = if_match.group(1)
                body, _ = _parse_block(child_lines, 0, indent)
                nodes.append(ScriptIf(condition=condition, body=body))
                i = next_i
                continue

            # Else if
            elif_match = re.match(r"else\s+if\s+(.+)$", header)
            if elif_match:
                condition = elif_match.group(1)
                body, _ = _parse_block(child_lines, 0, indent)
                nodes.append(ScriptElseIf(condition=condition, body=body))
                i = next_i
                continue

            # Else
            if header == "else":
                body, _ = _parse_block(child_lines, 0, indent)
                nodes.append(ScriptElse(body=body))
                i = next_i
                continue

            # Try
            if header == "try":
                body, _ = _parse_block(child_lines, 0, indent)
                nodes.append(ScriptTry(body=body))
                i = next_i
                continue

            # Catch
            catch_match = re.match(r"catch\s*\(([^)]*)\)$", header)
            if catch_match:
                param = catch_match.group(1).strip() or None
                body, _ = _parse_block(child_lines, 0, indent)
                nodes.append(ScriptCatch(param=param, body=body))
                i = next_i
                continue

            # Finally
            if header == "finally":
                body, _ = _parse_block(child_lines, 0, indent)
                nodes.append(ScriptFinally(body=body))
                i = next_i
                continue

            # Async function
            async_fn_match = re.match(r"async\s+(\w+)\s*\(([^)]*)\)$", header)
            if async_fn_match:
                name = async_fn_match.group(1)
                params = _parse_params(async_fn_match.group(2))
                body, _ = _parse_block(child_lines, 0, indent)
                nodes.append(
                    ScriptFunction(
                        name=name, params=params, is_async=True, body=body
                    )
                )
                i = next_i
                continue

            # Function (or method - same syntax)
            fn_match = re.match(r"(\w+)\s*\(([^)]*)\)$", header)
            if fn_match:
                name = fn_match.group(1)
                params = _parse_params(fn_match.group(2))
                body, _ = _parse_block(child_lines, 0, indent)
                nodes.append(
                    ScriptFunction(
                        name=name, params=params, is_async=False, body=body
                    )
                )
                i = next_i
                continue

            # Collection or nested object (fallback for unrecognized block headers)
            obj_str, col_next = _compile_collection_inline(
                parsed, i + 1, indent
            )
            eq_match = re.match(r"(.+?)\s*=\s*(.*)", header)
            if eq_match:
                lhs = eq_match.group(1)
                rhs = eq_match.group(2)
                if rhs:
                    value = f"{{{rhs}: {obj_str}}}"
                else:
                    value = obj_str
                nodes.append(ScriptCollection(lhs=lhs, value=value))
            else:
                # Bare collection (key: value inline in parent object)
                nodes.append(ScriptCollection(lhs=header, value=obj_str))
            i = col_next
            continue

        # --- Plain statement ---
        nodes.append(ScriptStatement(text=content))
        i += 1

    return nodes, i


def _parse_params(params_str: str) -> List[str]:
    """Parse a comma-separated parameter string into a list of parameter names."""
    params_str = params_str.strip()
    if not params_str:
        return []
    return [p.strip() for p in params_str.split(",")]


def _compile_collection_inline(
    parsed: List[Tuple[int, str, bool]], start: int, parent_indent: int
) -> Tuple[str, int]:
    """Compile indented block into either {object} or [array].

    Mirrors the compiler's _compile_collection_inline logic exactly.
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

        # standalone ":" -> object item separator in array
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


def _compile_template_inline(content: str, tmpl_type: str) -> str:
    """Compile inline template content (single line after html!: etc.)."""
    if tmpl_type in ("html!", "htm!"):
        return re.sub(r"(?<!\$)\{([^}]+)\}", r"${\1}", content)
    if tmpl_type == "text!":
        return re.sub(r"\{([^}]+)\}", r"${\1}", content)
    return content


def _compile_template_block(
    lines: List[Tuple[int, str, bool]], base_indent: int, tmpl_type: str
) -> str:
    """Compile a multi-line template block.

    Mirrors the compiler's _compile_template_block logic.
    """
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
        from .compiler import compile

        html = compile(nodes, data=None)
        html = html.rstrip("\n")
        html = re.sub(r"(?<!\$)\{([^}]+)\}", r"${\1}", html)
        if tmpl_type == "htm!":
            html = re.sub(r'="(\$\{[^}]+\})"', r"=\1", html)
        html = re.sub(r"\n\t*", "", html)
        return html

    if tmpl_type == "text!":
        text = "\\n".join(src_lines)
        text = re.sub(r"\{([^}]+)\}", r"${\1}", text)
        return text

    if tmpl_type == "table!":
        return _compile_table_literal(src_lines)

    return src.replace("\n", "\\n")


def _compile_table_literal(src_lines: List[str]) -> str:
    """Compile table!: block into a JS array of objects."""
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
