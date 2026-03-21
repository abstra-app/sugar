from dataclasses import dataclass


@dataclass
class Token:
    type: str  # "line", "blank", "comment"
    indent: int
    head: str  # before first colon, stripped
    text: str  # after first colon, stripped
    has_colon: bool
