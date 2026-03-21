from typing import List, Tuple

from .parser import IMPLICIT_CHILDREN
from .tokens import Token


def check(tokens: List[Token]) -> List[Tuple[int, str]]:
    warnings: List[Tuple[int, str]] = []
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

        # skip tokens inside script blocks
        if in_script:
            if indent <= script_indent:
                in_script = False
            else:
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
            warnings.append((
                line_num,
                f"'{tag_part}' can be shortened to '{short}' (div is implicit)",
            ))

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
                warnings.append((
                    line_num,
                    f"'{raw_tag}' is implicit inside '{parent_tag}'"
                    f" — use '{suggestion}' instead",
                ))

        # update parent stack
        if token.has_colon and not token.text:
            resolved_tag = raw_tag
            if not resolved_tag and parent_tag in IMPLICIT_CHILDREN:
                resolved_tag = IMPLICIT_CHILDREN[parent_tag]
            if resolved_tag:
                parent_stack.append((indent, resolved_tag))

    return warnings
