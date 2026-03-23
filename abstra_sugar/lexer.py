from typing import List

from .tokens import Token


def find_colon(line: str) -> int:
    depth = 0
    in_string: str | None = None  # tracks quote char: ' or "
    for i, ch in enumerate(line):
        # string tracking
        if in_string:
            if ch == in_string and (i == 0 or line[i - 1] != "\\"):
                in_string = None
            continue
        if ch in ('"', "'"):
            in_string = ch
            continue

        # depth tracking for (), {}, []
        if ch in ("(", "{", "["):
            depth += 1
        elif ch in (")", "}", "]"):
            depth -= 1
        elif ch == ":" and depth == 0:
            # skip :// (URLs)
            if line[i + 1 : i + 3] == "//":
                continue
            # position 0: only if followed by space (implicit child)
            if i == 0:
                if len(line) > 1 and line[1] == " ":
                    return i
                continue
            # separator colon: followed by space or end of string
            if i == len(line) - 1 or line[i + 1] == " ":
                return i
    return -1


def scan(code: str) -> List[Token]:
    tokens = []

    for raw_line in code.split("\n"):
        stripped = raw_line.strip()

        if not stripped:
            tokens.append(Token("blank", 0, "", "", False))
            continue

        indent = 0
        for ch in raw_line:
            if ch == " ":
                indent += 1
            else:
                break

        if stripped.startswith("# ") or stripped == "#":
            tokens.append(Token("comment", indent, stripped, "", False))
            continue

        colon_idx = find_colon(stripped)

        if colon_idx != -1:
            head = stripped[:colon_idx].rstrip()
            text = stripped[colon_idx + 1 :].strip()
            tokens.append(Token("line", indent, head, text, True))
        else:
            tokens.append(Token("line", indent, stripped, "", False))

    return tokens
