# HTML

Sugar uses indentation to represent HTML nesting. Each line defines an element.

## Elements

```sugar
div:
```
```html
<div></div>
```

## Classes

Use `.` to add classes, like CSS selectors:

```sugar
div.container.flex:
```
```html
<div class="container flex"></div>
```

## Attributes

Space-separated after the tag:

```sugar
input type=text placeholder=Name id=name-field:
a href=/about target=_blank: About
```
```html
<input type="text" placeholder="Name" id="name-field">
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

## Nesting

Indent children with tabs:

```sugar
div.card:
	h2: Title
	p: Description
	div.actions:
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

Lines starting with `#` are removed from output:

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
