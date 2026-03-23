import re
from typing import List

from .check import _find_matching
from .lexer import scan
from .parser import IMPLICIT_CHILDREN
from .tokens import Token


def format_source(source: str) -> str:
    lines = source.split("\n")
    tokens = scan(source)
    out: List[str] = []
    parent_stack: List[tuple] = []  # (indent, tag)
    in_script = False
    script_indent = -1
    skip_until = -1

    for idx, token in enumerate(tokens):
        if idx < skip_until:
            continue

        raw = lines[idx]

        if token.type != "line":
            out.append(raw)
            continue

        indent = token.indent
        head = token.head
        prefix = " " * indent

        # script block tracking
        if in_script:
            if indent <= script_indent:
                in_script = False
            else:
                # table!: inside script — align columns
                if _is_table_line(token):
                    formatted, consumed = _format_table_block(lines, tokens, idx)
                    out.extend(formatted)
                    skip_until = idx + consumed
                    continue
                formatted, consumed = _format_script_line(token, lines, tokens, idx)
                out.extend(formatted)
                skip_until = idx + consumed
                continue

        # parent stack
        while parent_stack and parent_stack[-1][0] >= indent:
            parent_stack.pop()
        parent_tag = parent_stack[-1][1] if parent_stack else ""

        # tag info
        parts = head.split()
        tag_part = parts[0] if parts else ""
        raw_tag = tag_part.split(".")[0].split("#")[0]

        # table!: in HTML context — align columns
        if _is_table_line(token):
            formatted, consumed = _format_table_block(lines, tokens, idx)
            out.extend(formatted)
            skip_until = idx + consumed
            continue

        # detect script entry
        if raw_tag == "script" and token.has_colon and not token.text:
            in_script = True
            script_indent = indent
            parent_stack.append((indent, raw_tag))
            out.append(raw)
            continue

        # 1. div is implicit
        if raw_tag == "div" and len(tag_part) > 3:
            short = tag_part[3:]
            rest_parts = parts[1:] if len(parts) > 1 else []
            new_head = " ".join([short] + rest_parts)
            if token.has_colon:
                out.append(
                    f"{prefix}{new_head}: {token.text}"
                    if token.text
                    else f"{prefix}{new_head}:"
                )
            else:
                out.append(f"{prefix}{new_head}")
        # 2. implicit child tag
        elif (
            parent_tag in IMPLICIT_CHILDREN and raw_tag == IMPLICIT_CHILDREN[parent_tag]
        ):
            rest = tag_part[len(raw_tag) :]
            rest_parts = parts[1:] if len(parts) > 1 else []
            if rest:
                new_head = " ".join([rest] + rest_parts)
            elif rest_parts:
                new_head = " ".join(rest_parts)
            else:
                new_head = ""
            if token.has_colon:
                if new_head:
                    out.append(
                        f"{prefix}{new_head}: {token.text}"
                        if token.text
                        else f"{prefix}{new_head}:"
                    )
                else:
                    out.append(
                        f"{prefix}: {token.text}" if token.text else f"{prefix}:"
                    )
            else:
                out.append(f"{prefix}{new_head}" if new_head else f"{prefix}{raw_tag}")
        else:
            out.append(raw)

        # update parent stack
        if token.has_colon and not token.text:
            resolved = raw_tag
            if not resolved and parent_tag in IMPLICIT_CHILDREN:
                resolved = IMPLICIT_CHILDREN[parent_tag]
            if resolved:
                parent_stack.append((indent, resolved))

    return "\n".join(out)


def _is_table_line(token: Token) -> bool:
    """Check if this token starts a table!: block."""
    if not (token.has_colon and not token.text):
        return False
    head = token.head
    if not head or "table!" not in head:
        return False
    # HTML: "table!" or "table!.class" or "table!#id"
    parts = head.split(".")[0].split("#")[0].split()
    if parts and parts[0] == "table!":
        return True
    # JS: "varname = table!"
    return "= table!" in head


def _format_table_block(lines: List[str], tokens: List[Token], start: int) -> tuple:
    """Format a table!: block with aligned | columns.

    Returns (output_lines, total_lines_consumed).
    """
    header_raw = lines[start]
    header_indent = tokens[start].indent
    child_indent = header_indent + 1
    result: List[str] = [header_raw]

    # collect child lines
    child_rows: List[List[str]] = []
    child_indices: List[int] = []
    j = start + 1
    while j < len(tokens):
        t = tokens[j]
        if t.type == "blank":
            j += 1
            continue
        if t.type != "line" or t.indent <= header_indent:
            break
        raw_content = lines[j].lstrip(" \t")
        cells = [c.strip() for c in raw_content.split("|")]
        child_rows.append(cells)
        child_indices.append(j)
        j += 1

    if not child_rows:
        return result, j - start

    # compute max width per column
    num_cols = max(len(row) for row in child_rows)
    col_widths = [0] * num_cols
    for row in child_rows:
        for ci, cell in enumerate(row):
            if ci < num_cols:
                col_widths[ci] = max(col_widths[ci], len(cell))

    # format each row with aligned columns
    prefix = " " * child_indent
    for row in child_rows:
        padded = []
        for ci in range(num_cols):
            cell = row[ci] if ci < len(row) else ""
            padded.append(cell.ljust(col_widths[ci]))
        result.append(prefix + " | ".join(padded).rstrip())

    return result, j - start


def _format_script_line(
    token: Token, lines: List[str], tokens: List[Token], idx: int
) -> tuple:
    """Format a single script line. Returns (output_lines, lines_consumed)."""
    indent = token.indent
    prefix = " " * indent
    # use raw line content (stripped of leading tabs) to preserve original spacing
    raw_content = lines[idx].lstrip(" \t")

    result_lines: List[str] = []

    # strip trailing semicolons
    raw_content = _strip_semicolon(raw_content)

    # replace arrow functions: (args) => with (args):
    raw_content = re.sub(r"\(([^)]*)\)\s*=>", r"(\1):", raw_content)

    # NOTE: function keyword removal requires block restructuring
    # (converting { body } to indented block) — not handled by formatter

    # inline object/array in assignment context
    assign_match = re.match(r"([\w.]+)\s*=\s*", raw_content)
    if assign_match:
        rhs_start = assign_match.end()
        rhs = raw_content[rhs_start:]
        varname = assign_match.group(1)

        # inline object: x = {key: val, ...}
        if rhs.startswith("{") and not rhs.startswith("${"):
            j = _find_matching(raw_content, rhs_start, "{", "}")
            if j != -1 and j == len(raw_content) - 1:
                inner = raw_content[rhs_start + 1 : j]
                if inner.strip() and ":" in inner:
                    expanded = _expand_object(inner, indent + 1)
                    result_lines.append(f"{prefix}{varname} =:")
                    result_lines.extend(expanded)
                    return result_lines, 1

        # inline array: x = [val, val, ...]
        if rhs.startswith("["):
            j = _find_matching(raw_content, rhs_start, "[", "]")
            if j != -1 and j == len(raw_content) - 1:
                inner = raw_content[rhs_start + 1 : j]
                if inner.strip() and "," in inner:
                    expanded = _expand_array(inner, indent + 1)
                    result_lines.append(f"{prefix}{varname} =:")
                    result_lines.extend(expanded)
                    return result_lines, 1

    result_lines.append(f"{prefix}{raw_content}")
    return result_lines, 1


def _strip_semicolon(content: str) -> str:
    s = content.rstrip()
    if s.endswith(";"):
        return s[:-1]
    return content


def _split_top_level(inner: str, sep: str = ",") -> List[str]:
    """Split string by separator at depth 0, respecting strings and brackets."""
    parts: List[str] = []
    depth = 0
    in_str: str | None = None
    current: List[str] = []

    for i, ch in enumerate(inner):
        if in_str:
            current.append(ch)
            if ch == in_str and (i == 0 or inner[i - 1] != "\\"):
                in_str = None
            continue
        if ch in ('"', "'", "`"):
            in_str = ch
            current.append(ch)
            continue
        if ch in ("(", "{", "["):
            depth += 1
        elif ch in (")", "}", "]"):
            depth -= 1
        if ch == sep and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)

    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def _expand_object(inner: str, depth: int) -> List[str]:
    """Expand object interior into indented key: value lines."""
    prefix = " " * depth
    entries = _split_top_level(inner)
    out: List[str] = []
    for entry in entries:
        out.append(f"{prefix}{entry}")
    return out


def _expand_array(inner: str, depth: int) -> List[str]:
    """Expand array interior into indented value lines."""
    prefix = " " * depth
    entries = _split_top_level(inner)
    out: List[str] = []
    for entry in entries:
        out.append(f"{prefix}{entry}")
    return out
