from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union


@dataclass
class ForBlock:
    var: str
    keyword: str  # "of" or "in"
    iterable: str
    children: List["HtmlChild"] = field(default_factory=list)


@dataclass
class IfBlock:
    condition: str
    children: List["HtmlChild"] = field(default_factory=list)


@dataclass
class ComponentDef:
    name: str
    params: List[str]
    children: List["HtmlChild"] = field(default_factory=list)


@dataclass
class ComponentCall:
    name: str
    args_raw: str
    children: List["HtmlChild"] = field(default_factory=list)  # slot content


@dataclass
class Element:
    tag: str
    classes: List[str] = field(default_factory=list)
    attributes: Dict[str, Union[str, bool]] = field(default_factory=dict)
    text: Optional[str] = None
    children: List["HtmlChild"] = field(default_factory=list)


HtmlChild = Union[Element, ForBlock, IfBlock, ComponentCall]


@dataclass
class StyleRule:
    selector: str
    properties: List[Tuple[str, str]] = field(default_factory=list)
    children: List["StyleRule"] = field(default_factory=list)


@dataclass
class StyleElement:
    classes: List[str] = field(default_factory=list)
    attributes: Dict[str, Union[str, bool]] = field(default_factory=dict)
    rules: List[StyleRule] = field(default_factory=list)


@dataclass
class ScriptElement:
    classes: List[str] = field(default_factory=list)
    attributes: Dict[str, Union[str, bool]] = field(default_factory=dict)
    body: str = ""


Node = Union[Element, StyleElement, ScriptElement, ForBlock, IfBlock, ComponentDef, ComponentCall]
