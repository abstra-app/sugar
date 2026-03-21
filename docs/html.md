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

Use `{expr}` to interpolate JavaScript expressions in dynamic contexts (for/if blocks):

```sugar
ul#list:
	for user of users:
		li: {user.name} ({user.email})
```

Inside dynamic blocks, `{expr}` compiles to `${expr}` in template literals, enabling dynamic content.

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

## Dynamic Rendering

### for loops

Use `for` inside an HTML element to generate repeated content:

```sugar
ul#users:
	for user of users:
		li: {user.name}
```

Compiles to a `<script>` that populates the element via `innerHTML`:

```html
<ul id="users"></ul>
<script>
	(function() {
		let _t = "";
		for (let user of users) {
			_t += `<li>${user.name}</li>`;
		}
		document.getElementById("users").innerHTML = _t;
	})();
</script>
```

### if conditionals

```sugar
#message:
	if error:
		p.text-red: {error}
```

### Nested loops

```sugar
table#data:
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
#links:
	for page of pages:
		a href=/page/{page.id}: {page.title}
```

Compiles to `<a href="/page/${page.id}">${page.title}</a>` inside the template literal.

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
