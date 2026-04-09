from typing import List

from lsprotocol import types

from ..parser import HTML_TAGS
from .state import DocumentState

_KEYWORDS = ["for", "if", "else", "while", "class", "style", "script", "slot"]

_JS_KEYWORDS = [
    "const", "let", "var", "return", "throw", "await", "async",
    "new", "typeof", "instanceof", "delete", "void", "super",
    "import", "export", "default", "from", "switch", "case",
    "break", "continue", "do", "yield", "try", "catch", "finally",
]

_CSS_PROPERTIES = [
    "color", "background", "background-color", "margin", "padding",
    "border", "border-radius", "display", "flex", "grid",
    "position", "top", "right", "bottom", "left",
    "width", "height", "min-width", "max-width", "min-height", "max-height",
    "font-size", "font-weight", "font-family", "line-height",
    "text-align", "text-decoration", "text-transform",
    "opacity", "overflow", "z-index", "cursor", "transition",
    "transform", "animation", "box-shadow", "gap",
    "justify-content", "align-items", "flex-direction",
]

_ATTR_VALUES = {
    "type": ["text", "password", "email", "number", "tel", "url",
             "date", "time", "checkbox", "radio", "file", "submit",
             "button", "hidden", "range", "color", "search"],
    "method": ["get", "post", "put", "delete", "patch"],
    "target": ["_blank", "_self", "_parent", "_top"],
    "rel": ["stylesheet", "icon", "preconnect", "noopener", "noreferrer"],
    "charset": ["UTF-8"],
}


def get_completions(
    state: DocumentState, line: int, character: int,
) -> List[types.CompletionItem]:
    lines = state.source.split("\n")
    if line >= len(lines):
        return []
    current_line = lines[line]
    prefix = current_line[:character].strip()
    context = _get_line_context(lines, line)
    items: List[types.CompletionItem] = []

    if context == "style":
        for prop in _CSS_PROPERTIES:
            if prop.startswith(prefix):
                items.append(types.CompletionItem(label=prop, kind=types.CompletionItemKind.Property))
        return items

    if context == "script":
        for kw in _JS_KEYWORDS:
            if kw.startswith(prefix):
                items.append(types.CompletionItem(label=kw, kind=types.CompletionItemKind.Keyword))
        return items

    # Check for attribute value context
    attr_match = prefix.rsplit("=", 1)
    if len(attr_match) == 2 and " " not in attr_match[0].split()[-1]:
        attr_name = attr_match[0].split()[-1]
        if attr_name in _ATTR_VALUES:
            for val in _ATTR_VALUES[attr_name]:
                items.append(types.CompletionItem(label=val, kind=types.CompletionItemKind.Value))
            return items

    # HTML context
    for tag in sorted(HTML_TAGS):
        if tag.startswith(prefix):
            items.append(types.CompletionItem(label=tag, kind=types.CompletionItemKind.Class))
    for kw in _KEYWORDS:
        if kw.startswith(prefix):
            items.append(types.CompletionItem(label=kw, kind=types.CompletionItemKind.Keyword))
    for name in state.components:
        if name.startswith(prefix):
            comp = state.components[name]
            params = ", ".join(comp.params)
            items.append(types.CompletionItem(
                label=name, kind=types.CompletionItemKind.Function, detail=f"{name}({params})",
            ))
    return items


def _get_line_context(lines: List[str], target_line: int) -> str:
    indent_at_target = len(lines[target_line]) - len(lines[target_line].lstrip()) if lines[target_line].strip() else 0
    current_indent = indent_at_target
    for i in range(target_line - 1, -1, -1):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            continue
        line_indent = len(line) - len(line.lstrip())
        if line_indent < current_indent:
            tag_part = stripped.split(".")[0].split("#")[0]
            parts = tag_part.split()
            tag = parts[0] if parts else ""
            if tag.startswith("style") and ":" in stripped:
                return "style"
            if tag.startswith("script") and ":" in stripped:
                return "script"
            current_indent = line_indent
            if line_indent == 0:
                break
    return "html"
