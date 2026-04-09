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
    body_nodes: List["ScriptNode"] = field(default_factory=list)


@dataclass
class TableLiteral:
    classes: List[str] = field(default_factory=list)
    attributes: Dict[str, Union[str, bool]] = field(default_factory=dict)
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)


@dataclass
class MarkdownLiteral:
    classes: List[str] = field(default_factory=list)
    attributes: Dict[str, Union[str, bool]] = field(default_factory=dict)
    source: str = ""


@dataclass
class MathLiteral:
    source: str = ""


@dataclass
class SvgLiteral:
    classes: List[str] = field(default_factory=list)
    attributes: Dict[str, Union[str, bool]] = field(default_factory=dict)
    source: str = ""


@dataclass
class Comment:
    text: str = ""


@dataclass
class ScriptFunction:
    name: str
    params: List[str]
    is_async: bool
    body: List["ScriptNode"]


@dataclass
class ScriptClass:
    name: str
    extends: Optional[str]
    methods: List["ScriptNode"]


@dataclass
class ScriptForLoop:
    var: str
    keyword: str  # "of" or "in"
    iterable: str
    body: List["ScriptNode"]


@dataclass
class ScriptWhileLoop:
    condition: str
    body: List["ScriptNode"]


@dataclass
class ScriptIf:
    condition: str
    body: List["ScriptNode"]


@dataclass
class ScriptElseIf:
    condition: str
    body: List["ScriptNode"]


@dataclass
class ScriptElse:
    body: List["ScriptNode"]


@dataclass
class ScriptTry:
    body: List["ScriptNode"]


@dataclass
class ScriptCatch:
    param: Optional[str]
    body: List["ScriptNode"]


@dataclass
class ScriptFinally:
    body: List["ScriptNode"]


@dataclass
class ScriptCollection:
    lhs: str
    value: str  # compiled inline "{...}" or "[...]"


@dataclass
class ScriptTemplateLiteral:
    prefix: str  # code before the html!/text!/etc
    literal_type: str  # "html!", "htm!", "text!", "table!"
    content: str  # compiled template content


@dataclass
class ScriptStatement:
    text: str


@dataclass
class ScriptComment:
    text: str


ScriptNode = Union[
    ScriptFunction,
    ScriptClass,
    ScriptForLoop,
    ScriptWhileLoop,
    ScriptIf,
    ScriptElseIf,
    ScriptElse,
    ScriptTry,
    ScriptCatch,
    ScriptFinally,
    ScriptCollection,
    ScriptTemplateLiteral,
    ScriptStatement,
    ScriptComment,
]


Node = Union[
    Element,
    StyleElement,
    ScriptElement,
    ForBlock,
    IfBlock,
    ComponentDef,
    ComponentCall,
    TableLiteral,
    MarkdownLiteral,
    MathLiteral,
    SvgLiteral,
    Comment,
]
