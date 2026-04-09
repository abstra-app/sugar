"""Semantic tokens provider for Sugar LSP.

Walks the raw token stream from scan() and emits delta-encoded semantic tokens
with (deltaLine, deltaCol, length, tokenTypeIndex, modifierMask) quintets.
"""

import re
from typing import List, Optional, Tuple

from ..lexer import scan
from ..parser import HTML_TAGS

TOKEN_TYPES = [
    "keyword",
    "function",
    "method",
    "variable",
    "string",
    "number",
    "comment",
    "operator",
    "property",
    "tag",
    "class",
    "type",
    "parameter",
    "macro",
]

TOKEN_MODIFIERS = [
    "declaration",
    "defaultLibrary",
    "id",
]

_TYPE_INDEX = {t: i for i, t in enumerate(TOKEN_TYPES)}
_MOD_BIT = {m: 1 << i for i, m in enumerate(TOKEN_MODIFIERS)}

# JS built-in globals
_JS_BUILTINS = {
    "console",
    "document",
    "window",
    "Math",
    "JSON",
    "Date",
    "Array",
    "Object",
    "String",
    "Number",
    "Boolean",
    "RegExp",
    "Map",
    "Set",
    "Promise",
    "Error",
    "parseInt",
    "parseFloat",
    "setTimeout",
    "setInterval",
    "clearTimeout",
    "clearInterval",
    "fetch",
    "alert",
    "confirm",
    "prompt",
    "encodeURIComponent",
    "decodeURIComponent",
    "isNaN",
    "isFinite",
    "Symbol",
    "WeakMap",
    "WeakSet",
    "Proxy",
    "Reflect",
    "Intl",
    "globalThis",
    "queueMicrotask",
    "structuredClone",
    "crypto",
    "performance",
    "navigator",
    "location",
    "history",
    "localStorage",
    "sessionStorage",
    "XMLHttpRequest",
    "WebSocket",
    "EventSource",
    "AbortController",
    "FormData",
    "URL",
    "URLSearchParams",
    "Headers",
    "Request",
    "Response",
    "Blob",
    "File",
    "FileReader",
    "ReadableStream",
    "WritableStream",
    "TransformStream",
    "TextEncoder",
    "TextDecoder",
    "MutationObserver",
    "IntersectionObserver",
    "ResizeObserver",
    "requestAnimationFrame",
    "cancelAnimationFrame",
}

_JS_CONSTANTS = {"true", "false", "null", "undefined"}

_JS_BLOCK_KEYWORDS = {"for", "if", "else", "while", "class", "try", "catch", "finally"}
_JS_STATEMENT_KEYWORDS = {
    "async",
    "await",
    "return",
    "throw",
    "new",
    "const",
    "let",
    "var",
    "export",
    "import",
    "from",
    "default",
    "switch",
    "case",
    "break",
    "continue",
    "do",
    "yield",
    "delete",
    "typeof",
    "instanceof",
    "void",
}
_MACRO_TAGS = {"table!", "markdown!", "math!", "svg!"}
_JS_MACROS = {"html!", "text!", "table!", "htm!"}


def _modifier_mask(*modifiers: str) -> int:
    mask = 0
    for m in modifiers:
        mask |= _MOD_BIT.get(m, 0)
    return mask


# ---- Raw token type helpers ----

RawToken = Tuple[int, int, int, int, int]  # (line, col, length, type_index, mod_mask)


def _emit(
    tokens: List[RawToken],
    line: int,
    col: int,
    length: int,
    token_type: str,
    *modifiers: str,
) -> None:
    """Append a raw (absolute) token to the list."""
    if length <= 0:
        return
    ti = _TYPE_INDEX.get(token_type, 0)
    mm = _modifier_mask(*modifiers)
    tokens.append((line, col, length, ti, mm))


def _delta_encode(raw_tokens: List[RawToken]) -> List[int]:
    """Convert absolute tokens to delta-encoded flat list."""
    # Sort by line, then col
    raw_tokens.sort(key=lambda t: (t[0], t[1]))
    result: List[int] = []
    prev_line = 0
    prev_col = 0
    for line, col, length, ti, mm in raw_tokens:
        dl = line - prev_line
        dc = col - prev_col if dl == 0 else col
        result.extend([dl, dc, length, ti, mm])
        prev_line = line
        prev_col = col
    return result


# ---- Context types ----

_CTX_HTML = "html"
_CTX_CSS = "css"
_CTX_SCRIPT = "script"


# ---- HTML tokenization ----


def _tokenize_html_line(
    tokens: List[RawToken],
    line_num: int,
    raw_line: str,
    indent: int,
    head: str,
    text: str,
    has_colon: bool,
) -> None:
    """Tokenize a single HTML-context line."""
    stripped = raw_line.strip()
    if not stripped:
        return

    # Comment
    if stripped.startswith("# ") or stripped == "#":
        _emit(tokens, line_num, indent, len(stripped), "comment")
        return

    # Component definition: name = (params):
    comp_def = re.match(r"(\w+)\s*=\s*\(([^)]*)\)$", head)
    if comp_def and has_colon:
        name = comp_def.group(1)
        params_str = comp_def.group(2)
        # function name with declaration
        name_col = indent
        _emit(tokens, line_num, name_col, len(name), "function", "declaration")
        # parameters
        if params_str.strip():
            params = [p.strip() for p in params_str.split(",")]
            paren_start = raw_line.index("(", indent)
            search_from = paren_start + 1
            for param in params:
                if not param:
                    continue
                pidx = raw_line.index(param, search_from)
                _emit(tokens, line_num, pidx, len(param), "parameter")
                search_from = pidx + len(param)
        # colon operator
        if has_colon:
            colon_col = raw_line.rindex(":")
            _emit(tokens, line_num, colon_col, 1, "operator")
        return

    # Component call: name(args) where name is not an HTML tag
    comp_call = re.match(r"(\w+)\s*\(([^)]*)\)$", head)
    if comp_call and comp_call.group(1) not in HTML_TAGS:
        name = comp_call.group(1)
        name_col = raw_line.index(name, indent)
        _emit(tokens, line_num, name_col, len(name), "function")
        # args as strings
        args_str = comp_call.group(2)
        if args_str.strip():
            paren_start = raw_line.index("(", name_col)
            _tokenize_string_args(tokens, line_num, paren_start + 1, args_str)
        if has_colon:
            colon_col = raw_line.rindex(":")
            _emit(tokens, line_num, colon_col, 1, "operator")
        return

    # Keywords: for x of items, if cond, else
    for_match = re.match(r"(for)\s+(.+?)\s+(of|in)\s+(.+)", head)
    if for_match:
        _emit_keyword_at(tokens, line_num, raw_line, indent, "for")
        kw2 = for_match.group(3)  # "of" or "in"
        # Find the keyword position
        _emit_keyword_after(tokens, line_num, raw_line, indent + 4, kw2)
        if has_colon:
            colon_col = raw_line.rindex(":")
            _emit(tokens, line_num, colon_col, 1, "operator")
        return

    if head.startswith("if ") or head == "else":
        kw = "if" if head.startswith("if ") else "else"
        _emit_keyword_at(tokens, line_num, raw_line, indent, kw)
        if has_colon:
            colon_col = raw_line.rindex(":")
            _emit(tokens, line_num, colon_col, 1, "operator")
        return

    if head == "slot":
        _emit(tokens, line_num, indent, len("slot"), "keyword")
        if has_colon:
            colon_col = raw_line.rindex(":")
            _emit(tokens, line_num, colon_col, 1, "operator")
        return

    # Macro tags: table!, markdown!, math!, svg!
    tag_part = head.split()[0] if head else ""
    base_tag = tag_part.split(".")[0].split("#")[0]
    if base_tag in _MACRO_TAGS:
        tag_col = indent
        _emit(tokens, line_num, tag_col, len(base_tag), "macro")
        # classes/ids on macro
        _tokenize_tag_classes_ids(tokens, line_num, indent + len(base_tag), tag_part[len(base_tag):])
        if has_colon:
            colon_col = raw_line.rindex(":")
            _emit(tokens, line_num, colon_col, 1, "operator")
        return

    # Regular HTML element: tag.class#id attr=val: text
    _tokenize_html_element(tokens, line_num, raw_line, indent, head, text, has_colon)


def _tokenize_html_element(
    tokens: List[RawToken],
    line_num: int,
    raw_line: str,
    indent: int,
    head: str,
    text: str,
    has_colon: bool,
) -> None:
    """Tokenize a regular HTML element line."""
    if not head:
        return

    parts = _split_respecting_parens(head)
    if not parts:
        return

    tag_part = parts[0]

    # Parse tag.class1.class2#id
    _tokenize_tag_selector(tokens, line_num, indent, tag_part)

    # Attributes
    col_offset = indent + len(tag_part)
    for attr in parts[1:]:
        # find attr in raw_line from col_offset
        attr_col = raw_line.find(attr, col_offset)
        if attr_col == -1:
            attr_col = col_offset
        if "=" in attr:
            eq_idx = attr.index("=")
            key = attr[:eq_idx]
            val = attr[eq_idx + 1:]
            _emit(tokens, line_num, attr_col, len(key), "property")
            if val:
                _emit(tokens, line_num, attr_col + eq_idx + 1, len(val), "string")
        else:
            _emit(tokens, line_num, attr_col, len(attr), "property")
        col_offset = attr_col + len(attr)

    # Colon
    if has_colon:
        colon_col = _find_separator_colon(raw_line)
        if colon_col >= 0:
            _emit(tokens, line_num, colon_col, 1, "operator")

    # Text content — look for {interpolations}
    if text:
        text_start = raw_line.find(text, indent)
        if text_start >= 0:
            _tokenize_interpolations(tokens, line_num, text_start, text)


def _tokenize_tag_selector(
    tokens: List[RawToken],
    line_num: int,
    col: int,
    tag_part: str,
) -> None:
    """Tokenize a tag selector like 'div.foo.bar#baz'."""
    if not tag_part:
        return

    # Split by . and #, preserving delimiters
    segments: List[Tuple[str, str]] = []  # (prefix, text) where prefix is '.', '#', or ''
    current = ""
    current_prefix = ""
    for ch in tag_part:
        if ch in (".", "#"):
            if current:
                segments.append((current_prefix, current))
            current_prefix = ch
            current = ""
        else:
            current += ch
    if current:
        segments.append((current_prefix, current))

    offset = col
    for prefix, text in segments:
        if prefix == "":
            # tag name
            _emit(tokens, line_num, offset, len(text), "tag")
            offset += len(text)
        elif prefix == ".":
            # .class
            _emit(tokens, line_num, offset, 1 + len(text), "class")
            offset += 1 + len(text)
        elif prefix == "#":
            # #id
            _emit(tokens, line_num, offset, 1 + len(text), "type", "id")
            offset += 1 + len(text)


def _tokenize_tag_classes_ids(
    tokens: List[RawToken],
    line_num: int,
    col: int,
    suffix: str,
) -> None:
    """Tokenize .class and #id suffixes after a tag/macro name."""
    if not suffix:
        return
    offset = col
    current = ""
    current_type: Optional[str] = None
    for ch in suffix:
        if ch in (".", "#"):
            if current and current_type:
                if current_type == "class":
                    _emit(tokens, line_num, offset - len(current), len(current), "class")
                elif current_type == "id":
                    _emit(tokens, line_num, offset - len(current), len(current), "type", "id")
            current = ch
            current_type = "class" if ch == "." else "id"
            offset += 1
        else:
            current += ch
            offset += 1
    if current and current_type:
        full_len = len(current)
        start = offset - len(current)
        if current_type == "class":
            _emit(tokens, line_num, start, full_len, "class")
        elif current_type == "id":
            _emit(tokens, line_num, start, full_len, "type", "id")


def _tokenize_interpolations(
    tokens: List[RawToken],
    line_num: int,
    text_start: int,
    text: str,
) -> None:
    """Find {expr} interpolations in text and emit variable tokens."""
    for m in re.finditer(r"\{([^}]+)\}", text):
        brace_col = text_start + m.start()
        # Emit the whole {expr} as variable
        _emit(tokens, line_num, brace_col, m.end() - m.start(), "variable")


def _tokenize_string_args(
    tokens: List[RawToken],
    line_num: int,
    start_col: int,
    args_str: str,
) -> None:
    """Tokenize string arguments in component calls."""
    for m in re.finditer(r'("[^"]*"|\'[^\']*\')', args_str):
        col = start_col + m.start()
        _emit(tokens, line_num, col, len(m.group(0)), "string")


def _emit_keyword_at(
    tokens: List[RawToken],
    line_num: int,
    raw_line: str,
    start: int,
    keyword: str,
) -> None:
    """Emit a keyword token at or after start position."""
    idx = raw_line.find(keyword, start)
    if idx >= 0:
        _emit(tokens, line_num, idx, len(keyword), "keyword")


def _emit_keyword_after(
    tokens: List[RawToken],
    line_num: int,
    raw_line: str,
    start: int,
    keyword: str,
) -> None:
    """Emit a keyword token searching from start position using word boundaries."""
    # Search for keyword as a whole word
    pattern = r"\b" + re.escape(keyword) + r"\b"
    for m in re.finditer(pattern, raw_line):
        if m.start() >= start:
            _emit(tokens, line_num, m.start(), len(keyword), "keyword")
            return


def _find_separator_colon(raw_line: str) -> int:
    """Find the position of the separator colon in a raw line.
    This mirrors the lexer's find_colon but on the raw line."""
    from ..lexer import find_colon

    stripped = raw_line.strip()
    idx = find_colon(stripped)
    if idx < 0:
        return -1
    indent = len(raw_line) - len(raw_line.lstrip())
    return indent + idx


def _split_respecting_parens(s: str) -> List[str]:
    """Split string by spaces, respecting parentheses."""
    parts: List[str] = []
    current: List[str] = []
    depth = 0
    in_string: Optional[str] = None
    for ch in s:
        if in_string:
            current.append(ch)
            if ch == in_string:
                in_string = None
            continue
        if ch in ('"', "'"):
            in_string = ch
            current.append(ch)
            continue
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


# ---- CSS tokenization ----


def _tokenize_css_line(
    tokens: List[RawToken],
    line_num: int,
    raw_line: str,
    indent: int,
    head: str,
    text: str,
    has_colon: bool,
    is_selector: bool,
) -> None:
    """Tokenize a single CSS-context line."""
    stripped = raw_line.strip()
    if not stripped:
        return

    # Comment
    if stripped.startswith("# ") or stripped == "#":
        _emit(tokens, line_num, indent, len(stripped), "comment")
        return

    # @-rules
    if stripped.startswith("@"):
        word = stripped.split()[0] if stripped.split() else stripped
        _emit(tokens, line_num, indent, len(word), "keyword")
        if has_colon:
            colon_col = raw_line.rindex(":")
            _emit(tokens, line_num, colon_col, 1, "operator")
        return

    # Mixin definition: name = ():
    mixin_def = re.match(r"(\w+)\s*=\s*\(([^)]*)\)$", head)
    if mixin_def and has_colon:
        name = mixin_def.group(1)
        _emit(tokens, line_num, indent, len(name), "function", "declaration")
        if has_colon:
            colon_col = raw_line.rindex(":")
            _emit(tokens, line_num, colon_col, 1, "operator")
        return

    # Mixin call: +name or name()
    if head.startswith("+"):
        name = head[1:]
        _emit(tokens, line_num, indent, len(head), "function")
        return

    if is_selector:
        # Selector line — emit as class
        _emit(tokens, line_num, indent, len(head), "class")
        if has_colon:
            colon_col = raw_line.rindex(":")
            _emit(tokens, line_num, colon_col, 1, "operator")
        return

    # Property: value
    if has_colon and text:
        _emit(tokens, line_num, indent, len(head), "property")
        text_col = raw_line.find(text, indent + len(head))
        if text_col >= 0:
            _emit(tokens, line_num, text_col, len(text), "string")
        # colon
        colon_col = raw_line.find(":", indent + len(head))
        if colon_col >= 0:
            _emit(tokens, line_num, colon_col, 1, "operator")
        return

    if has_colon and not text:
        # Could be selector
        _emit(tokens, line_num, indent, len(head), "class")
        colon_col = raw_line.rindex(":")
        _emit(tokens, line_num, colon_col, 1, "operator")
        return

    # Bare property without colon
    _emit(tokens, line_num, indent, len(stripped), "property")


# ---- JS/Script tokenization ----


def _tokenize_script_line(
    tokens: List[RawToken],
    line_num: int,
    raw_line: str,
) -> None:
    """Tokenize a single JS-context line."""
    stripped = raw_line.strip()
    if not stripped:
        return
    indent = len(raw_line) - len(raw_line.lstrip())

    # Comment
    if stripped.startswith("//"):
        _emit(tokens, line_num, indent, len(stripped), "comment")
        return

    # Class definition: class Name [extends Base]:
    cls_match = re.match(r"(class)\s+(\w+)(?:\s+(extends)\s+(\w+))?\s*:?$", stripped)
    if cls_match:
        _emit_keyword_at(tokens, line_num, raw_line, indent, "class")
        name = cls_match.group(2)
        name_col = raw_line.find(name, indent + 5)
        _emit(tokens, line_num, name_col, len(name), "class", "declaration")
        if cls_match.group(3):
            ext_col = raw_line.find("extends", name_col)
            _emit(tokens, line_num, ext_col, len("extends"), "keyword")
            base = cls_match.group(4)
            base_col = raw_line.find(base, ext_col + 7)
            _emit(tokens, line_num, base_col, len(base), "class")
        if stripped.endswith(":"):
            colon_col = raw_line.rindex(":")
            _emit(tokens, line_num, colon_col, 1, "operator")
        return

    # Async function def: async name(params):
    async_fn = re.match(r"(async)\s+(\w+)\s*\(([^)]*)\)\s*:$", stripped)
    if async_fn:
        _emit_keyword_at(tokens, line_num, raw_line, indent, "async")
        name = async_fn.group(2)
        name_col = raw_line.find(name, indent + 5)
        _emit(tokens, line_num, name_col, len(name), "function", "declaration")
        _tokenize_fn_params(tokens, line_num, raw_line, name_col + len(name), async_fn.group(3))
        colon_col = raw_line.rindex(":")
        _emit(tokens, line_num, colon_col, 1, "operator")
        return

    # Function/method def: name(params):
    fn_match = re.match(r"(\w+)\s*\(([^)]*)\)\s*:$", stripped)
    if fn_match:
        name = fn_match.group(1)
        if name not in _JS_BLOCK_KEYWORDS and name not in _JS_STATEMENT_KEYWORDS:
            name_col = raw_line.find(name, indent)
            _emit(tokens, line_num, name_col, len(name), "function", "declaration")
            _tokenize_fn_params(tokens, line_num, raw_line, name_col + len(name), fn_match.group(2))
            colon_col = raw_line.rindex(":")
            _emit(tokens, line_num, colon_col, 1, "operator")
            return

    # For loop: for x of/in items:
    for_match = re.match(r"(for)\s+(.+?)\s+(of|in)\s+(.+?)(?::)?$", stripped)
    if for_match:
        _emit_keyword_at(tokens, line_num, raw_line, indent, "for")
        kw2 = for_match.group(3)
        _emit_keyword_after(tokens, line_num, raw_line, indent + 4, kw2)
        if stripped.endswith(":"):
            colon_col = raw_line.rindex(":")
            _emit(tokens, line_num, colon_col, 1, "operator")
        _tokenize_script_inline_parts(tokens, line_num, raw_line, indent)
        return

    # Block keywords with arguments: if cond:, while cond:, catch(e):
    for kw in ("if", "else if", "while", "else", "try", "finally"):
        if stripped == kw + ":" or stripped.startswith(kw + " "):
            _emit_keyword_at(tokens, line_num, raw_line, indent, kw.split()[0])
            if kw == "else if":
                _emit_keyword_after(tokens, line_num, raw_line, indent + 5, "if")
            if stripped.endswith(":"):
                colon_col = raw_line.rindex(":")
                _emit(tokens, line_num, colon_col, 1, "operator")
            _tokenize_script_inline_parts(tokens, line_num, raw_line, indent + len(kw))
            return

    # catch(param):
    catch_match = re.match(r"(catch)\s*\(([^)]*)\)\s*:?$", stripped)
    if catch_match:
        _emit_keyword_at(tokens, line_num, raw_line, indent, "catch")
        param = catch_match.group(2).strip()
        if param:
            paren_col = raw_line.find("(", indent)
            param_col = raw_line.find(param, paren_col)
            _emit(tokens, line_num, param_col, len(param), "parameter")
        if stripped.endswith(":"):
            colon_col = raw_line.rindex(":")
            _emit(tokens, line_num, colon_col, 1, "operator")
        return

    # Template macro: ... html!: or ... table!:
    for macro in _JS_MACROS:
        macro_col = _find_word(raw_line, macro, indent)
        if macro_col >= 0:
            _emit(tokens, line_num, macro_col, len(macro), "macro")

    # Collection operator =:
    if "=:" in stripped:
        eq_col = raw_line.find("=:")
        if eq_col >= 0:
            _emit(tokens, line_num, eq_col, 2, "operator")

    # Now tokenize inline parts (strings, numbers, keywords, builtins)
    _tokenize_script_inline_parts(tokens, line_num, raw_line, indent)

    # Trailing colon as block opener
    if stripped.endswith(":") and not stripped.endswith("::"):
        # Check it's not in a string or after =:
        last_colon = raw_line.rindex(":")
        # Don't re-emit if it's part of =:
        if last_colon > 0 and raw_line[last_colon - 1] == "=":
            pass
        else:
            _emit(tokens, line_num, last_colon, 1, "operator")


def _tokenize_fn_params(
    tokens: List[RawToken],
    line_num: int,
    raw_line: str,
    start: int,
    params_str: str,
) -> None:
    """Tokenize function parameter names."""
    if not params_str.strip():
        return
    paren_col = raw_line.find("(", start)
    if paren_col < 0:
        return
    params = [p.strip() for p in params_str.split(",")]
    search_from = paren_col + 1
    for param in params:
        if not param:
            continue
        # Handle default values: param = value
        param_name = param.split("=")[0].strip()
        pidx = raw_line.find(param_name, search_from)
        if pidx >= 0:
            _emit(tokens, line_num, pidx, len(param_name), "parameter")
            search_from = pidx + len(param_name)


def _find_word(s: str, word: str, start: int = 0) -> int:
    """Find a word in string, return its position or -1."""
    idx = s.find(word, start)
    return idx


def _tokenize_script_inline_parts(
    tokens: List[RawToken],
    line_num: int,
    raw_line: str,
    start: int,
) -> None:
    """Tokenize inline parts: strings, numbers, keywords, builtins, template vars."""
    # Strings: "..." and '...'
    for m in re.finditer(r"""(?:"[^"\\]*(?:\\.[^"\\]*)*"|'[^'\\]*(?:\\.[^'\\]*)*')""", raw_line):
        if m.start() >= start or m.start() >= len(raw_line) - len(raw_line.lstrip()):
            _emit(tokens, line_num, m.start(), len(m.group(0)), "string")

    # Numbers
    for m in re.finditer(r"\b(\d+(?:\.\d+)?)\b", raw_line):
        if m.start() >= len(raw_line) - len(raw_line.lstrip()):
            _emit(tokens, line_num, m.start(), len(m.group(0)), "number")

    # Template ${expr}
    for m in re.finditer(r"\$\{([^}]+)\}", raw_line):
        if m.start() >= len(raw_line) - len(raw_line.lstrip()):
            _emit(tokens, line_num, m.start(), len(m.group(0)), "variable")

    # Statement keywords
    for kw in _JS_STATEMENT_KEYWORDS:
        for m in re.finditer(r"\b" + re.escape(kw) + r"\b", raw_line):
            if m.start() >= len(raw_line) - len(raw_line.lstrip()):
                _emit(tokens, line_num, m.start(), len(kw), "keyword")

    # Constants
    for const in _JS_CONSTANTS:
        for m in re.finditer(r"\b" + re.escape(const) + r"\b", raw_line):
            if m.start() >= len(raw_line) - len(raw_line.lstrip()):
                _emit(tokens, line_num, m.start(), len(const), "keyword", "defaultLibrary")

    # Built-ins
    for m in re.finditer(r"\b(\w+)\b", raw_line):
        if m.start() >= len(raw_line) - len(raw_line.lstrip()):
            word = m.group(1)
            if word in _JS_BUILTINS:
                _emit(tokens, line_num, m.start(), len(word), "variable", "defaultLibrary")


# ---- Main entry point ----


def get_semantic_tokens(source: str) -> List[int]:
    """Return delta-encoded semantic tokens for the given Sugar source."""
    raw_tokens: List[RawToken] = []
    lines = source.split("\n")
    scan_tokens = scan(source)

    # Identify script/style blocks by scanning tokens first
    # The raw scan() gives us 1 token per source line
    # We need to figure out which ranges are script/style

    # Approach: Walk source lines directly, using scan tokens for structure info
    # Maintain context based on indent levels

    # First pass: identify script/style block ranges
    block_ranges: List[Tuple[int, int, str]] = []  # (start_line, end_line, ctx_type)
    i = 0
    while i < len(scan_tokens):
        tok = scan_tokens[i]
        if tok.type == "line" and tok.has_colon and not tok.text:
            head_parts = tok.head.split()
            tag = head_parts[0].split(".")[0].split("#")[0] if head_parts else ""
            if tag == "style":
                block_indent = tok.indent
                start = i + 1
                end = start
                while end < len(scan_tokens):
                    t = scan_tokens[end]
                    if t.type == "line" and t.indent <= block_indent:
                        break
                    end += 1
                block_ranges.append((start, end, _CTX_CSS))
                i = end
                continue
            elif tag == "script":
                block_indent = tok.indent
                start = i + 1
                end = start
                while end < len(scan_tokens):
                    t = scan_tokens[end]
                    if t.type == "line" and t.indent <= block_indent:
                        break
                    end += 1
                block_ranges.append((start, end, _CTX_SCRIPT))
                i = end
                continue
        i += 1

    # Build a line_num -> context map
    line_context = {}
    for start, end, ctx in block_ranges:
        for ln in range(start, end):
            line_context[ln] = ctx

    # Now tokenize each line
    for line_idx in range(len(lines)):
        raw_line = lines[line_idx]
        if line_idx >= len(scan_tokens):
            break

        tok = scan_tokens[line_idx]
        ctx = line_context.get(line_idx, _CTX_HTML)

        if ctx == _CTX_HTML:
            if tok.type == "line":
                _tokenize_html_line(
                    raw_tokens,
                    line_idx,
                    raw_line,
                    tok.indent,
                    tok.head,
                    tok.text,
                    tok.has_colon,
                )
            elif tok.type == "comment":
                _emit(raw_tokens, line_idx, tok.indent, len(raw_line.strip()), "comment")
        elif ctx == _CTX_CSS:
            if tok.type == "line":
                # Determine if this is a selector (has children) or property
                is_selector = tok.has_colon and not tok.text
                # Look ahead to see if next line is indented more
                if is_selector and line_idx + 1 < len(scan_tokens):
                    next_tok = scan_tokens[line_idx + 1]
                    if next_tok.type != "blank" and next_tok.indent > tok.indent:
                        is_selector = True
                    else:
                        is_selector = False
                _tokenize_css_line(
                    raw_tokens,
                    line_idx,
                    raw_line,
                    tok.indent,
                    tok.head,
                    tok.text,
                    tok.has_colon,
                    is_selector,
                )
            elif tok.type == "comment":
                _emit(raw_tokens, line_idx, tok.indent, len(raw_line.strip()), "comment")
        elif ctx == _CTX_SCRIPT:
            _tokenize_script_line(raw_tokens, line_idx, raw_line)

    return _delta_encode(raw_tokens)
