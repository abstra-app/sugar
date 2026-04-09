# Sugar LSP — Design Spec

## Overview

A full Language Server Protocol implementation for the Sugar template language, providing AST-based semantic highlighting, diagnostics, completion, go-to-definition, hover, and document symbols in Neovim (and any LSP-compatible editor).

Lives inside the existing `abstra_sugar` package at `abstra_sugar/lsp/`. Reuses the existing lexer, parser, and AST. Communicates via stdio. Started with `abstra-sugar lsp`.

## Architecture

### Directory structure

```
abstra_sugar/
├── ast.py                      # existing + new ScriptNode types
├── lexer.py                    # existing (unchanged)
├── parser.py                   # existing (unchanged)
├── compiler.py                 # refactored to compile from ScriptNode AST
├── script_parser.py            # NEW: parses script body → List[ScriptNode]
├── script_parser_test.py       # NEW: tests for script parser
├── cli.py                      # NEW: entry point for `abstra-sugar` command
├── lsp/
│   ├── __init__.py
│   ├── __main__.py             # `python -m abstra_sugar.lsp` (alternative entry)
│   ├── server.py               # pygls LanguageServer, registers capabilities
│   ├── server_test.py          # integration tests with pygls test client
│   ├── state.py                # document state: AST/token cache per open file
│   ├── state_test.py
│   ├── semantic_tokens.py      # semantic tokens provider
│   ├── semantic_tokens_test.py
│   ├── diagnostics.py          # syntax error diagnostics
│   ├── diagnostics_test.py
│   ├── completion.py           # context-aware autocomplete
│   ├── completion_test.py
│   ├── definition.py           # go-to-definition for components
│   ├── definition_test.py
│   ├── hover.py                # hover info
│   ├── hover_test.py
│   ├── symbols.py              # document symbols / outline
│   └── symbols_test.py
└── ...
```

### Dependencies

- `pygls` — Python Generic Language Server (protocol handling, JSON-RPC, lifecycle)
- `lsprotocol` — LSP type definitions (installed with pygls)

Added to `requirements.txt`. No other new dependencies.

### Entry point

`setup.py` gains a console_scripts entry:

```python
entry_points={
    "console_scripts": [
        "abstra-sugar=abstra_sugar.cli:main",
    ],
},
```

`abstra_sugar/cli.py`:

```python
import sys

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "lsp":
        from .lsp.server import create_server
        server = create_server()
        server.start_io()
    else:
        print("Usage: abstra-sugar lsp")
        sys.exit(1)
```

### Neovim configuration

`editors/vim/lsp.lua`:

```lua
vim.filetype.add({ extension = { sugar = "sugar" } })

local lspconfig = require("lspconfig")
local configs = require("lspconfig.configs")

configs.sugar = {
  default_config = {
    cmd = { "abstra-sugar", "lsp" },
    filetypes = { "sugar" },
    root_dir = lspconfig.util.find_git_ancestor,
  },
}

lspconfig.sugar.setup({})
```

## Script AST (new)

Today the parser emits `ScriptElement(body: str)` — the script body is a raw string. The compiler re-parses this string in `_compile_script_body`. This must change.

### New AST nodes

Added to `abstra_sugar/ast.py`:

```python
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
    methods: List["ScriptFunction"]

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
    entries: list

@dataclass
class ScriptTemplateLiteral:
    prefix: str
    literal_type: str  # "html!", "htm!", "text!", "table!"
    children: List[Node]  # parsed Sugar AST for html!/htm!

@dataclass
class ScriptStatement:
    text: str

@dataclass
class ScriptComment:
    text: str

ScriptNode = Union[
    ScriptFunction, ScriptClass, ScriptForLoop, ScriptWhileLoop,
    ScriptIf, ScriptElseIf, ScriptElse,
    ScriptTry, ScriptCatch, ScriptFinally,
    ScriptCollection, ScriptTemplateLiteral,
    ScriptStatement, ScriptComment,
]
```

### New module: `script_parser.py`

Extracts the parsing logic currently embedded in `compiler.py`'s `_compile_script_body`. Takes the raw script body string and produces `List[ScriptNode]`.

Handles:
- Function/method definitions: `name(args):` → `ScriptFunction`
- Async functions: `async name(args):` → `ScriptFunction(is_async=True)`
- Class definitions: `class Name:` / `class Name extends Base:` → `ScriptClass`
- For loops: `for x of items:` / `for key in obj:` → `ScriptForLoop`
- While loops: `while cond:` → `ScriptWhileLoop`
- If/else if/else: → `ScriptIf`, `ScriptElseIf`, `ScriptElse`
- Try/catch/finally: → `ScriptTry`, `ScriptCatch`, `ScriptFinally`
- Collections: `name =:` + indented children → `ScriptCollection`
- Template literals: `html!:`, `htm!:`, `text!:`, `table!:` → `ScriptTemplateLiteral`
- Inline arrows: `(args): expr` — detected within `ScriptStatement`
- List comprehensions: `[expr for x of items if cond]` — detected within `ScriptStatement`
- Comments: `// ...` → `ScriptComment`
- Everything else: → `ScriptStatement`

### Parser integration

`parser.py` gains a small change: after extracting the script body string, it calls `script_parser.parse_script(body_str)` to produce `List[ScriptNode]`, which is stored in `ScriptElement.body` (type changes from `str` to `List[ScriptNode]`).

### Compiler refactor

`_compile_script_body` is refactored to do a visitor walk over `List[ScriptNode]` instead of re-parsing the raw string. All existing behavior preserved — validated by running the existing snapshot tests.

## State Management

`abstra_sugar/lsp/state.py`:

```python
@dataclass
class DocumentState:
    uri: str
    source: str
    version: int
    tokens: List[Token]
    ast: List[Node]
    components: Dict[str, ComponentDef]
    diagnostics: List[Diagnostic]
```

- Uses `TextDocumentSyncKind.Incremental` — pygls handles applying incremental edits to the in-memory source
- Re-runs `scan()` + `parse()` after each `didChange`
- Caches AST per document URI
- Publishes diagnostics after each parse
- If `parse()` raises an exception, catches it and converts to a Diagnostic at the error line

## Features

### Semantic Tokens

Traverses the full AST (HTML, CSS, and Script) and emits typed tokens with exact positions.

#### HTML context

| Element | Token Type | Modifiers |
|---|---|---|
| tag name (`div`, `input`) | `tag` | |
| class (`.foo`) | `class` | |
| id (`#bar`) | `type` | `id` |
| attribute key | `property` | |
| attribute value | `string` | |
| interpolation `{expr}` | `variable` | |
| `for`, `if`, `of`, `in` | `keyword` | |
| comment `#` | `comment` | |
| `slot` | `keyword` | |
| `:` separator | `operator` | |

#### CSS context (inside `style:`)

| Element | Token Type | Modifiers |
|---|---|---|
| selector | `class` | |
| property name | `property` | |
| property value | `string` | |
| `@media`, `@keyframes` | `keyword` | |
| mixin def name | `function` | `declaration` |
| mixin call `@name()` | `function` | |
| CSS color `#fff` | `number` | |
| CSS function `rgb()`, `calc()` | `function` | |

#### JS context (inside `script:`)

| Element | Token Type | Modifiers |
|---|---|---|
| function def name | `function` | `declaration` |
| method def name | `method` | `declaration` |
| class name | `class` | `declaration` |
| extends target | `class` | |
| params | `parameter` | |
| `for`, `if`, `else`, `while`, `class`, `try`, `catch`, `finally` | `keyword` | |
| `async`, `await`, `return`, `throw`, `new`, `const`, `let`, `var` | `keyword` | |
| `of`, `in`, `extends` | `keyword` | |
| arrow `():` (the `:` as `=>`) | `operator` | |
| string `"..."`, `'...'` | `string` | |
| template literal `` ` `` | `string` | |
| `${expr}` in template | `variable` | |
| numbers | `number` | |
| `true`, `false`, `null`, `undefined` | `keyword` | `defaultLibrary` |
| `console`, `document`, `Math`, `JSON` | `variable` | `defaultLibrary` |
| `html!`, `text!`, `table!`, `htm!` | `macro` | |
| comment `//` | `comment` | |
| collection `=:` | `operator` | |
| list comprehension `for`/`of`/`if` | `keyword` | |

#### Component context

| Element | Token Type | Modifiers |
|---|---|---|
| def name (`card = (...)`) | `function` | `declaration` |
| call name (`card(...)`) | `function` | |
| params in def | `parameter` | |
| args in call | `string` | |

#### Special literals

| Element | Token Type | Modifiers |
|---|---|---|
| `table!`, `markdown!`, `math!`, `svg!` | `macro` | |
| Sugar HTML inside `html!:` in script | recursive — same HTML tokens | |

### Diagnostics

Published after each parse. Sources:

- **Syntax errors**: exceptions from `scan()` or `parse()` → Error severity, positioned at the offending line
- **Undefined component**: component called but not defined in the document → Warning
- **Unknown HTML tag**: tag not in `HTML_TAGS` and not a component → Hint

### Completion

Context-aware, triggered by typing:

- **Line start (HTML)**: HTML tags, defined components, keywords (`for`, `if`, `style`, `script`)
- **After `.`**: CSS classes already used in the document
- **Inside `style:`**: CSS property names, selectors used in the document
- **Inside `script:`**: JS keywords, variables/functions defined in scope
- **After `=` in attribute**: common values for that attribute (`type=` → `text`, `password`, `email`, etc.)

### Go-to-definition

- Component call → component definition (same file, v1)
- Multi-file support deferred to future version

### Hover

- HTML tag → element description
- Component → `name(param1, param2)` with definition location
- CSS property → (future: MDN reference)

### Document Symbols

Hierarchical outline via `DocumentSymbol`:

- Top-level elements (html, head, body)
- Component definitions (with params)
- Style rules
- Script functions and classes (with methods)

## Testing

Every module has an adjacent `_test.py` file.

### `script_parser_test.py`

One test per construct: function, async function, class, class+extends, method, constructor, for-of, for-in, while, if, else-if, else, try, catch, finally, collection (object), collection (array), collection (array of objects), nested object, template literal (html!, text!, table!), inline arrow, list comprehension, comment, plain statement.

Each test provides a script body string, runs the parser, and asserts the exact AST node types and fields.

### `semantic_tokens_test.py`

One test per row in the token tables above. Each test provides a `.sugar` snippet, runs the semantic tokens provider, and asserts the exact list of `(line, col, length, token_type, modifiers)`.

### `diagnostics_test.py`

Tests with intentional errors: bad indentation, missing colon, undefined component call, unknown tag. Asserts diagnostic message, severity, and range.

### `completion_test.py`

Tests per context: line start suggestions, after `.`, inside style block, inside script block, after `=` in attribute. Asserts completion items and their kinds.

### `definition_test.py`

Test: component call resolves to component definition line/column. Test: unknown name returns no result.

### `hover_test.py`

Test: hover on tag, hover on component call, hover on component def.

### `symbols_test.py`

Test: full document produces correct symbol hierarchy.

### `server_test.py`

Integration tests using pygls test client. Sends `initialize`, `didOpen`, `didChange`, then calls `textDocument/semanticTokens/full`, `textDocument/completion`, `textDocument/definition`, `textDocument/hover`, `textDocument/documentSymbol`. Validates full round-trip.

### Regression: existing snapshot tests

After the compiler refactor, all existing snapshot tests (`abstra_sugar/snapshots/*.sugar` → `*.html`) must continue to pass with identical output. Zero regressions.
