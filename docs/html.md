# HTML

Sugar uses indentation to represent HTML nesting. Each line defines an element.

## Elements

```sugar
div:
```
```html
<div></div>
```

## Implicit div

Lines starting with `.` or `#` default to `div`:

```sugar
.container:
#main:
.flex.gap-4:
#app.wrapper:
```
```html
<div class="container"></div>
<div id="main"></div>
<div class="flex gap-4"></div>
<div id="app" class="wrapper"></div>
```

## Classes

Use `.` to add classes, like CSS selectors:

```sugar
div.container.flex:
```
```html
<div class="container flex"></div>
```

## ID shorthand

Use `#` after the tag name (or alone for implicit div):

```sugar
div#main:
canvas#game:
#app:
#sidebar.hidden:
```
```html
<div id="main"></div>
<canvas id="game"></canvas>
<div id="app"></div>
<div id="sidebar" class="hidden"></div>
```

## Attributes

Space-separated after the tag:

```sugar
input type=text placeholder=Name:
a href=/about target=_blank: About
```
```html
<input type="text" placeholder="Name">
<a href="/about" target="_blank">About</a>
```

Boolean attributes (no value):

```sugar
script module:
input disabled:
```
```html
<script module></script>
<input disabled>
```

## Text Content

Text goes after the colon:

```sugar
h1: Hello World
p: This is a paragraph
```
```html
<h1>Hello World</h1>
<p>This is a paragraph</p>
```

## Interpolation

Use `{expr}` to interpolate Python expressions when data is provided:

```python
sugar("h1: Hello {name}", {"name": "World"})
# → <h1>Hello World</h1>
```

Works in text content and attribute values:

```sugar
a href=/users/{user.id}: {user.name}
```

Expressions are evaluated against the data dict. Dot access works on nested dicts:

```python
sugar("p: {user.name}", {"user": {"name": "Alice"}})
# → <p>Alice</p>
```

Built-in functions like `len`, `str`, `int`, `sorted`, etc. are available in expressions.

## Nesting

Indent children with tabs:

```sugar
.card:
	h2: Title
	p: Description
	.actions:
		button: Save
		button: Cancel
```
```html
<div class="card">
	<h2>Title</h2>
	<p>Description</p>
	<div class="actions">
		<button>Save</button>
		<button>Cancel</button>
	</div>
</div>
```

## Inline Elements

Elements can be nested inline using colon-separated syntax:

```sugar
td: a href=/users/1: Edit User
p: span.bold: Important
```
```html
<td><a href="/users/1">Edit User</a></td>
<p><span class="bold">Important</span></p>
```

## Templating

Sugar supports server-side templating when a data dict is provided to `sugar()`.

### for loops

Iterate over collections to generate repeated HTML:

```sugar
ul:
	for user of users:
		li: {user.name}
```

```python
sugar(template, {"users": [{"name": "Alice"}, {"name": "Bob"}]})
```

```html
<ul>
	<li>Alice</li>
	<li>Bob</li>
</ul>
```

### if conditionals

Conditionally render elements:

```sugar
div:
	if show_message:
		p: Hello!
```

### Nested loops

```sugar
table:
	for group of groups:
		tr:
			th: {group.name}
		for item of group.items:
			tr:
				td: {item.key}
				td: {item.value}
```

### Interpolation in attributes

```sugar
div:
	for page of pages:
		a href=/page/{page.id}: {page.title}
```

## Implicit Children

Inside certain parent elements, children inherit the expected tag automatically:

| Parent | Implicit child |
|---|---|
| `ul`, `ol`, `menu` | `li` |
| `select`, `datalist` | `option` |
| `tr` | `td` |
| `thead` | `th` |
| `dl` | `dt` |
| `nav` | `a` |

```sugar
ul:
	: Home
	: About
	.active: Contact

select:
	value=br: Brasil
	value=us selected: USA
```
```html
<ul>
	<li>Home</li>
	<li>About</li>
	<li class="active">Contact</li>
</ul>
<select>
	<option value="br">Brasil</option>
	<option value="us" selected>USA</option>
</select>
```

Classes (`.class`), IDs (`#id`), and attributes (`attr=val`) on implicit children work naturally — the implicit tag is prepended.

## Void Elements

Self-closing elements (br, hr, img, input, meta, link, etc.) don't need a closing tag:

```sugar
hr:
br:
img src=logo.png alt=Logo:
meta charset=UTF-8:
```
```html
<hr>
<br>
<img src="logo.png" alt="Logo">
<meta charset="UTF-8">
```

## Comments

Lines starting with `# ` (hash followed by space) are removed from output:

```sugar
div:
	# This won't appear in the HTML
	p: Visible
```
```html
<div>
	<p>Visible</p>
</div>
```

Note: `#foo` (no space) is an ID shorthand, not a comment.
