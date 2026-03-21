# Sugar

A template language that compiles to HTML, CSS, and JavaScript. Combines the best ideas from Pug, Stylus, and CoffeeScript into a single indentation-based syntax.

## Install

```bash
pip install abstra_sugar
```

## Usage

```python
from abstra_sugar import sugar

html = sugar(open("page.sugar").read())
```

## Example

```sugar
html:
    head:
        style:
            .title:
                color: #333
                font-size: 24px
    body:
        h1.title: Hello World
        p: Welcome to Sugar
        ul:
            li: Simple
            li: Fast
            li: Clean
        script:
            greet(name):
                console.log(`Hello, ${name}!`)
            greet("World")
```

Compiles to:

```html
<html>
    <head>
        <style>
            .title {
                color: #333;
                font-size: 24px;
            }
        </style>
    </head>
    <body>
        <h1 class="title">Hello World</h1>
        <p>Welcome to Sugar</p>
        <ul>
            <li>Simple</li>
            <li>Fast</li>
            <li>Clean</li>
        </ul>
        <script>
            function greet(name) {
                console.log(`Hello, ${name}!`);
            }
            greet("World");
        </script>
    </body>
</html>
```

## Syntax Overview

| Feature | Sugar | Compiles to |
|---|---|---|
| Element | `div:` | `<div></div>` |
| Class | `div.foo.bar:` | `<div class="foo bar"></div>` |
| Attribute | `a href=/about:` | `<a href="/about"></a>` |
| Text | `h1: Hello` | `<h1>Hello</h1>` |
| Inline element | `td: a href=#: Click` | `<td><a href="#">Click</a></td>` |
| Void element | `hr:` | `<hr>` |
| Comment | `# ignored` | *(removed)* |
| CSS property | `color: red` | `color: red;` |
| CSS selector | `.foo:` | `.foo {` |
| Function | `greet(x):` | `function greet(x) {` |
| Arrow | `(x):` | `(x) => {` |
| Inline arrow | `(x): x * 2` | `(x) => x * 2` |
| For loop | `for x of arr:` | `for (let x of arr) {` |
| If | `if x > 0:` | `if (x > 0) {` |
| Class | `class Foo:` | `class Foo {` |
| Object | indented key/values | `{key: value, ...}` |

## Documentation

See the [docs](docs/) folder for the full language reference.

## Architecture

```
sugar(string) → string

    scan(code)    →  List[Token]      # lexer.py
    parse(tokens) →  List[Node]       # parser.py
    compile(nodes) → string           # compiler.py
```

## License

MIT — see [LICENSE](LICENSE).
