# JavaScript

Inside a `script:` element, Sugar compiles indentation-based syntax to JavaScript. Expressions stay as-is — only block structure (`:` → `{}`) and semicolons are handled.

## Functions

```sugar
script:
 greet(name):
  console.log(`Hello, ${name}!`)

 async fetchData(url):
  res = await fetch(url)
  return await res.json()
```
```js
function greet(name) {
 console.log(`Hello, ${name}!`);
}

async function fetchData(url) {
 res = await fetch(url);
 return await res.json();
}
```

## Arrow Functions

### Block arrows

Parenthesized params followed by `:` with indented body:

```sugar
script:
 items.forEach(
  (item):
   console.log(item)
 )
```
```js
items.forEach(
 (item) => {
  console.log(item);
 }
);
```

### Inline arrows

Params, `:`, and expression on the same line:

```sugar
script:
 nums.map((x): x * 2)
 setTimeout((): console.log("done"), 1000)
```
```js
nums.map((x) => x * 2);
setTimeout(() => console.log("done"), 1000);
```

### Trailing arrows

Arrow as the last argument of a function call:

```sugar
script:
 document.addEventListener("click", (e):
  console.log(e.target)
 )
```
```js
document.addEventListener("click", (e) => {
 console.log(e.target);
}
);
```

## Control Flow

### if / else if / else

```sugar
script:
 if x > 10:
  console.log("big")
 else if x > 5:
  console.log("medium")
 else:
  console.log("small")
```
```js
if (x > 10) {
 console.log("big");
} else if (x > 5) {
 console.log("medium");
} else {
 console.log("small");
}
```

### for loops

```sugar
script:
 for item of items:
  console.log(item)

 for key in obj:
  console.log(key)
```
```js
for (let item of items) {
 console.log(item);
}

for (let key in obj) {
 console.log(key);
}
```

### while

```sugar
script:
 while queue.length > 0:
  process(queue.shift())
```
```js
while (queue.length > 0) {
 process(queue.shift());
}
```

## Classes

```sugar
script:
 class Animal:
  constructor(name):
   this.name = name

  speak():
   console.log(`${this.name} makes a noise`)

 class Dog extends Animal:
  speak():
   console.log(`${this.name} barks`)
```
```js
class Animal {
 constructor(name) {
  this.name = name;
 }

 speak() {
  console.log(`${this.name} makes a noise`);
 }
}

class Dog extends Animal {
 speak() {
  console.log(`${this.name} barks`);
 }
}
```

## Error Handling

```sugar
script:
 try:
  data = JSON.parse(input)
 catch(e):
  console.error(e)
 finally:
  cleanup()
```
```js
try {
 data = JSON.parse(input);
} catch(e) {
 console.error(e);
} finally {
 cleanup();
}
```

## Object Literals

### Nested objects (inline key)

Objects can be defined using indentation with the first key on the assignment line:

```sugar
script:
 config = theme:
  colors:
   primary: "#6366f1"
   accent: "#22d3ee"
  spacing:
   sm: 8
   md: 16
```
```js
config = {theme: {colors: {primary: "#6366f1", accent: "#22d3ee"}, spacing: {sm: 8, md: 16}}};
```

### Flat object assignment (=:)

Use `=:` with indented `key: value` lines to create a flat object:

```sugar
script:
 point =:
  x: 100
  y: 200

 config =:
  debug: true
  verbose: false
  maxRetries: 3
```
```js
point = {x: 100, y: 200};
config = {debug: true, verbose: false, maxRetries: 3};
```

### Inline objects

Standard JS object syntax also works:

```sugar
script:
 point = {x: 10, y: 20}
```
```js
point = {x: 10, y: 20};
```

Note: prefer indented syntax (`=:` or nested) for multi-key objects over inline `{}` on a single line.

## Arrays

### Array with =:

Bare values under `=:` (without `key:` syntax) create an array:

```sugar
script:
 colors =:
  "red"
  "green"
  "blue"
```
```js
colors = ["red", "green", "blue"];
```

### Array of objects

Use standalone `:` as an item separator to create an array of objects:

```sugar
script:
 users =:
  :
   name: "Alice"
   age: 30
  :
   name: "Bob"
   age: 25
```
```js
users = [{name: "Alice", age: 30}, {name: "Bob", age: 25}];
```

## List Comprehensions

Python-style list comprehensions compile to `map` and `filter` chains:

```sugar
script:
 doubled = [x * 2 for x of nums]
 positives = [x for x of nums if x > 0]
 squaredPos = [x * x for x of nums if x > 0]
 upper = [s.toUpperCase() for s of names]
```
```js
doubled = nums.map((x) => x * 2);
positives = nums.filter((x) => x > 0).map((x) => x);
squaredPos = nums.filter((x) => x > 0).map((x) => x * x);
upper = names.map((s) => s.toUpperCase());
```

Syntax: `[expr for var of iterable]` or `[expr for var of iterable if condition]`.

## table!

`table!:` in a script block creates an array of objects from pipe-separated tabular data. The first row defines the keys:

```sugar
script:
 users = table!:
  name    | age | active
  "Alice" | 30  | true
  "Bob"   | 25  | false
  "Eve"   | 35  | true
```
```js
users = [{name: "Alice", age: 30, active: true}, {name: "Bob", age: 25, active: false}, {name: "Eve", age: 35, active: true}];
```

## text!

`text!:` creates a multiline template literal from indented raw text:

```sugar
script:
 greeting = text!:
  Hello, world!
  This is raw text.
  No quotes needed.

 message = text!:
  User {name} logged in.
  Welcome back!
```
```js
greeting = `Hello, world!\nThis is raw text.\nNo quotes needed.`;
message = `User ${name} logged in.\nWelcome back!`;
```

Lines are joined with `\n`. `{expr}` is converted to `${expr}` in the template literal.

## Template Literals with html!

Inside script blocks, use `html!:` to write sugar HTML that compiles to a JS template literal string:

```sugar
script:
 render():
  container.innerHTML += html!:
   .card.p-4:
    h3: {item.name}
    p.text-gray-400: {item.desc}
```

Compiles to:

```js
function render() {
 container.innerHTML += `<div class="card p-4"><h3>${item.name}</h3><p class="text-gray-400">${item.desc}</p></div>`;
}
```

`{expr}` inside `html!:` blocks becomes `${expr}` in the template literal. Attributes with interpolation also work: `a href=/users/{id}:` → `<a href="/users/${id}">`.

This replaces verbose inline HTML template strings with sugar syntax.

## Semicolons

Semicolons are inserted automatically. Lines ending with `{`, `(`, or `;` are left as-is.

## Comments

`#` comments inside script blocks are preserved as `//` comments in the output:

```sugar
script:
 # This is a comment
 console.log("visible")
```
```js
//This is a comment
console.log("visible");
```

## Blank Lines

Blank lines in the source are preserved in the output, keeping code readable.

## Script Attributes

```sugar
script module:
script type=module src=app.js:
```
```html
<script module></script>
<script type="module" src="app.js"></script>
```
