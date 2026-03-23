import re
from typing import Any, Dict, List, Tuple

from .lexer import scan
from .parser import IMPLICIT_CHILDREN
from .tokens import Token

Diagnostic = Dict[str, Any]

# Arrow function: (args) => ... — Sugar uses (args): instead
_ARROW_RE = re.compile(r"\([^)]*\)\s*=>")

# function keyword: function name(...) — Sugar uses name():
_FUNCTION_RE = re.compile(r"\bfunction\s+\w+\s*\(")

# Anonymous function: function(...) — Sugar uses ():
_ANON_FUNCTION_RE = re.compile(r"\bfunction\s*\(")


def check_source(source: str) -> List[Diagnostic]:
    tokens = scan(source)
    return _check_tokens(tokens)


def _emit(
    results: List[Diagnostic], line: int, msg: str, level: str = "warning"
) -> None:
    results.append({"line": line, "message": msg, "level": level})


def _find_matching(content: str, start: int, open_ch: str, close_ch: str) -> int:
    """Find matching closing bracket, respecting strings and nesting."""
    depth = 1
    in_str: str | None = None
    i = start + 1
    while i < len(content):
        ch = content[i]
        if in_str:
            if ch == in_str and content[i - 1] != "\\":
                in_str = None
        elif ch in ('"', "'", "`"):
            in_str = ch
        elif ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def _check_script_line(
    results: List[Diagnostic], line: int, content: str
) -> None:
    # scan for inline objects/arrays — only in assignment context
    # e.g. "x = {a: 1}" or "x = [1, 2]", not "x || {a: 1}" or "for i of [1,2]"
    assign_match = re.match(r"[\w.]+\s*=\s*", content)
    if assign_match:
        rhs_start = assign_match.end()
        rhs = content[rhs_start:]
        if rhs.startswith("{") and not rhs.startswith("${"):
            j = _find_matching(content, rhs_start, "{", "}")
            if j != -1 and j == len(content) - 1:
                inner = content[rhs_start + 1 : j]
                if inner.strip() and ":" in inner:
                    _emit(
                        results, line,
                        f"inline object — use indented notation instead",
                    )
        elif rhs.startswith("["):
            j = _find_matching(content, rhs_start, "[", "]")
            if j != -1 and j == len(content) - 1:
                inner = content[rhs_start + 1 : j]
                if inner.strip() and "," in inner:
                    _emit(
                        results, line,
                        f"inline list — use indented notation instead",
                    )

    # 5. trailing semicolons
    if content.rstrip().endswith(";"):
        _emit(results, line, "semicolons are unnecessary in Sugar")
    # 6. arrow functions
    if _ARROW_RE.search(content):
        _emit(
            results, line,
            "'() =>' is verbose — use '():' instead",
        )
    # 7. function keyword
    if _FUNCTION_RE.search(content):
        _emit(
            results, line,
            "'function name()' is verbose — use 'name():' instead",
        )
    elif _ANON_FUNCTION_RE.search(content):
        _emit(
            results, line,
            "'function()' is verbose — use '():' instead",
        )


def _check_tokens(tokens: List[Token]) -> List[Diagnostic]:
    warnings: List[Diagnostic] = []
    line_num = 0
    parent_stack: List[Tuple[int, str]] = []  # (indent, tag)
    in_script = False
    script_indent = -1

    for token in tokens:
        line_num += 1

        if token.type != "line":
            continue

        head = token.head
        indent = token.indent

        # check tokens inside script blocks for inline objects/arrays
        if in_script:
            if indent <= script_indent:
                in_script = False
            else:
                line_content = (
                    f"{token.head}: {token.text}" if token.has_colon
                    else token.head
                )
                _check_script_line(warnings, line_num, line_content)
                continue

        # track parent context
        while parent_stack and parent_stack[-1][0] >= indent:
            parent_stack.pop()
        parent_tag = parent_stack[-1][1] if parent_stack else ""

        # extract tag info
        parts = head.split()
        tag_part = parts[0] if parts else ""
        raw_tag = tag_part.split(".")[0].split("#")[0]

        # detect script block entry
        if raw_tag == "script" and token.has_colon and not token.text:
            in_script = True
            script_indent = indent
            parent_stack.append((indent, raw_tag))
            continue

        # 1. explicit div when implicit would work
        if raw_tag == "div" and len(tag_part) > 3:
            short = tag_part[3:]
            _emit(
                warnings, line_num,
                f"'{tag_part}' can be shortened to '{short}' (div is implicit)",
            )

        # 2. explicit child tag when parent has implicit mapping
        if parent_tag in IMPLICIT_CHILDREN:
            expected = IMPLICIT_CHILDREN[parent_tag]
            if raw_tag == expected:
                rest = tag_part[len(expected):]
                if rest:
                    suggestion = rest
                elif token.text:
                    suggestion = f": {token.text}"
                else:
                    suggestion = ":"
                _emit(
                    warnings, line_num,
                    f"'{raw_tag}' is implicit inside '{parent_tag}'"
                    f" — use '{suggestion}' instead",
                )

        # update parent stack
        if token.has_colon and not token.text:
            resolved_tag = raw_tag
            if not resolved_tag and parent_tag in IMPLICIT_CHILDREN:
                resolved_tag = IMPLICIT_CHILDREN[parent_tag]
            if resolved_tag:
                parent_stack.append((indent, resolved_tag))

    return warnings
