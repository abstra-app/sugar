# Sugar

A template language that compiles to HTML, CSS, and JavaScript. Combines the best ideas from Pug, Stylus, and CoffeeScript into a single indentation-based syntax.

## Install

```bash
pip install abstra-sugar
```

## Usage

```python
from abstra_sugar import sugar

# static
html = sugar(open("page.sugar").read())

# with data (templating)
html = sugar(open("page.sugar").read(), {"users": [...], "title": "Home"})
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
| Implicit div | `.foo:` | `<div class="foo"></div>` |
| ID shorthand | `#main:` | `<div id="main"></div>` |
| Combined | `canvas#game.full:` | `<canvas id="game" class="full"></canvas>` |
| Class | `div.foo.bar:` | `<div class="foo bar"></div>` |
| Attribute | `a href=/about:` | `<a href="/about"></a>` |
| Text | `h1: Hello` | `<h1>Hello</h1>` |
| Interpolation | `li: {user.name}` | `<li>Alice</li>` *(with data)* |
| Inline element | `td: a href=#: Click` | `<td><a href="#">Click</a></td>` |
| Void element | `hr:` | `<hr>` |
| Comment | `# ignored` | *(removed)* |
| Template for | `for x of arr:` | repeats children *(with data)* |
| Template if | `if cond:` | conditional render *(with data)* |
| CSS property | `color: red` | `color: red;` |
| CSS selector | `.foo:` | `.foo {` |
| JS function | `greet(x):` | `function greet(x) {` |
| JS arrow | `(x):` | `(x) => {` |
| JS inline arrow | `(x): x * 2` | `(x) => x * 2` |
| JS for loop | `for x of arr:` | `for (let x of arr) {` |
| JS if | `if x > 0:` | `if (x > 0) {` |
| JS class | `class Foo:` | `class Foo {` |
| JS object | indented key/values | `{key: value, ...}` |

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
