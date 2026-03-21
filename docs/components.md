# Components & Mixins

Sugar supports reusable components in HTML and mixins in CSS, using function-like syntax.

## HTML Components

### Defining

```sugar
card = (title):
	.bg-gray-900.rounded-2xl.p-6:
		h3: {title}
		slot:
```

- `name = (params):` defines a component
- `{param}` interpolates parameters
- `slot:` marks where children go

### Using

```sugar
card("Users"):
	ul:
		li: Alice
		li: Bob

card("Settings"):
	p: Nothing here yet
```

### Output

```html
<div class="bg-gray-900 rounded-2xl p-6">
	<h3>Users</h3>
	<ul>
		<li>Alice</li>
		<li>Bob</li>
	</ul>
</div>
<div class="bg-gray-900 rounded-2xl p-6">
	<h3>Settings</h3>
	<p>Nothing here yet</p>
</div>
```

### Multiple params

```sugar
link = (href, label):
	a.text-blue.underline href={href}: {label}

link("/about", "About Us")
link("/contact", "Contact")
```

### Components without slot

```sugar
avatar = (name):
	.w-10.h-10.rounded-full.bg-blue.flex.items-center.justify-center:
		span: {name[0]}

avatar("Alice")
```

## CSS Mixins

### Defining

```sugar
style:
	reset = ():
		margin: 0
		padding: 0
		box-sizing: border-box
```

### Using

Call with `@name()` inside any rule:

```sugar
style:
	reset = ():
		margin: 0
		padding: 0
		box-sizing: border-box

	body:
		@reset()
		font-family: sans-serif

	.card:
		@reset()
		border: 1px solid #ddd
```

### Output

```css
body {
	margin: 0;
	padding: 0;
	box-sizing: border-box;
	font-family: sans-serif;
}
.card {
	margin: 0;
	padding: 0;
	box-sizing: border-box;
	border: 1px solid #ddd;
}
```

Mixin definitions are removed from the output — only their expansions appear.
