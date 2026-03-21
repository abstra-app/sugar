" Vim syntax file for Sugar template language
" Language: Sugar
" Maintainer: Abstra

if exists("b:current_syntax")
  finish
endif

" Comments
syn match sugarComment /# .*$/ contains=@Spell

" Strings
syn region sugarString start=/"/ skip=/\\"/ end=/"/
syn region sugarString start=/'/ skip=/\\'/ end=/'/
syn region sugarTemplate start=/`/ skip=/\\`/ end=/`/ contains=sugarInterp
syn match sugarInterp /\${[^}]*}/ contained

" Interpolation in text (sugar-style)
syn match sugarTextInterp /{[^}]\+}/

" Numbers
syn match sugarNumber /\<\d\+\(\.\d\+\)\?\>/

" Boolean / null
syn keyword sugarBoolean true false
syn keyword sugarNull null undefined

" HTML tags
syn keyword sugarTag html head body div span p a ul ol li table thead tbody
syn keyword sugarTag tr td th h1 h2 h3 h4 h5 h6 img input button form
syn keyword sugarTag label select option textarea header footer main nav
syn keyword sugarTag section article aside meta link title style script
syn keyword sugarTag canvas br hr pre code blockquote iframe video audio
syn keyword sugarTag source figure figcaption details summary dialog
syn keyword sugarTag slot

" HTML void elements (no children)
syn keyword sugarVoid hr br img input meta link source track wbr col embed

" CSS properties (inside style blocks)
syn match sugarCSSProp /\<\(margin\|padding\|border\|background\|color\|font\|display\|position\|width\|height\|top\|left\|right\|bottom\|overflow\|opacity\|transform\|transition\|animation\|flex\|grid\|gap\|align\|justify\|text\|box\|z-index\|cursor\|outline\|resize\|content\|visibility\|white-space\|word\|letter\|line-height\|vertical-align\|float\|clear\|min-width\|max-width\|min-height\|max-height\|border-radius\|box-shadow\|backdrop-filter\)\>/

" CSS at-rules
syn match sugarAtRule /@\(keyframes\|media\|import\|font-face\|supports\)\>/

" CSS mixin call
syn match sugarMixinCall /@\w\+(.*)/

" JS keywords (inside script blocks)
syn keyword sugarJSKeyword if else for while class extends return new async
syn keyword sugarJSKeyword await try catch finally throw typeof instanceof
syn keyword sugarJSKeyword const let var this import export default from
syn keyword sugarJSKeyword function of in switch case break continue do

" Component definition
syn match sugarComponentDef /\w\+\s*=\s*([^)]*):/ contains=sugarString

" Component call
syn match sugarComponentCall /^\s*\w\+\s*([^)]*)/

" Attributes
syn match sugarAttr /\<\w\+=[^ \t:]*/
syn keyword sugarBoolAttr module disabled checked selected required readonly

" Class shorthand (.class)
syn match sugarClass /\.\([a-zA-Z_-][a-zA-Z0-9_:/.+-]*\)/

" ID shorthand (#id)
syn match sugarID /#\([a-zA-Z_-][a-zA-Z0-9_-]*\)/

" Colon separator
syn match sugarColon /:\s*$/
syn match sugarColon /:\s/

" Highlighting
hi def link sugarComment Comment
hi def link sugarString String
hi def link sugarTemplate String
hi def link sugarInterp Special
hi def link sugarTextInterp Special
hi def link sugarNumber Number
hi def link sugarBoolean Boolean
hi def link sugarNull Constant
hi def link sugarTag Keyword
hi def link sugarVoid Keyword
hi def link sugarCSSProp Type
hi def link sugarAtRule PreProc
hi def link sugarMixinCall PreProc
hi def link sugarJSKeyword Statement
hi def link sugarComponentDef Function
hi def link sugarComponentCall Function
hi def link sugarAttr Identifier
hi def link sugarBoolAttr Identifier
hi def link sugarClass Type
hi def link sugarID Identifier
hi def link sugarColon Delimiter

let b:current_syntax = "sugar"
