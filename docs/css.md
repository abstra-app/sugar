# CSS

Inside a `style:` element, Sugar uses indentation-based CSS inspired by Stylus.

## Basic Syntax

Selectors end with `:` and contain indented properties. Properties use `property: value` syntax.

```sugar
style:
	body:
		margin: 0
		font-family: sans-serif
	.container:
		max-width: 1200px
		padding: 0 20px
```
```html
<style>
	body {
		margin: 0;
		font-family: sans-serif;
	}
	.container {
		max-width: 1200px;
		padding: 0 20px;
	}
</style>
```

## Nested Selectors

Selectors can be nested:

```sugar
style:
	.card:
		border: 1px solid #ddd
		.header:
			font-weight: bold
		.body:
			padding: 16px
```
```html
<style>
	.card {
		border: 1px solid #ddd;
	}
	.card .header {
		font-weight: bold;
	}
	.card .body {
		padding: 16px;
	}
</style>
```

## Pseudo-selectors

CSS pseudo-selectors starting with `:` or `::` work naturally:

```sugar
style:
	a:hover:
		text-decoration: underline
	::selection:
		background: #b3d4fc
	::-webkit-scrollbar:
		width: 8px
```

## At-rules

Media queries, keyframes, and other at-rules:

```sugar
style:
	@keyframes fadeIn:
		from:
			opacity: 0
		to:
			opacity: 1
	@media (max-width: 768px):
		.sidebar:
			display: none
```

## Attributes

The style tag accepts attributes like any other element:

```sugar
style type=text/css:
	body:
		color: #333
```
