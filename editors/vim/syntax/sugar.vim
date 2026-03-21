" Vim syntax file for Sugar template language
" Language: Sugar
" Maintainer: Abstra

if exists("b:current_syntax")
  finish
endif

syn case match

" ============================================================
" GLOBAL (all contexts)
" ============================================================

" Comments: # followed by space
syn match sugarComment /# .*$/ containedin=ALL

" Strings
syn region sugarString start=/"/ skip=/\\"/ end=/"/ contained containedin=ALL
syn region sugarString start=/'/ skip=/\\'/ end=/'/ contained containedin=ALL

" Template literals with ${} interpolation
syn region sugarTemplateLit start=/`/ skip=/\\`/ end=/`/ contained containedin=ALL contains=sugarTemplateExpr
syn match sugarTemplateExpr /\${[^}]*}/ contained

" Sugar interpolation {expr}
syn match sugarInterp /{[^}]\+}/ containedin=ALL

" Numbers
syn match sugarNumber /\<\d\+\(\.\d\+\)\?\>/ containedin=ALL

" Colon separator (end of line or before space)
syn match sugarColon /:\ze\s/ containedin=ALL
syn match sugarColon /:\s*$/ containedin=ALL

" ============================================================
" HTML CONTEXT (default)
" ============================================================

" HTML tags
syn keyword sugarTag a abbr address article aside audio b bdi bdo blockquote
syn keyword sugarTag body br button canvas caption cite code col colgroup
syn keyword sugarTag data datalist dd del details dfn dialog div dl dt em
syn keyword sugarTag embed fieldset figcaption figure footer form
syn keyword sugarTag h1 h2 h3 h4 h5 h6 head header hgroup hr html
syn keyword sugarTag i iframe img input ins kbd label legend li link
syn keyword sugarTag main map mark menu meta meter nav noscript object
syn keyword sugarTag ol optgroup option output p picture pre progress
syn keyword sugarTag q rp rt ruby s samp section select slot small
syn keyword sugarTag source span strong sub summary sup
syn keyword sugarTag table tbody td template textarea tfoot th thead time
syn keyword sugarTag title tr track u ul var video wbr

" Void elements (distinct color)
syn keyword sugarVoid hr br img input meta link source track wbr col embed area base param

" Slot element
syn keyword sugarSlot slot

" Class shorthand: .class-name (possibly chained .a.b.c)
syn match sugarClass /\.[a-zA-Z_-][a-zA-Z0-9_:/.+-]*/

" ID shorthand: #id-name
syn match sugarID /#[a-zA-Z_-][a-zA-Z0-9_-]*/

" Attributes: key=value
syn match sugarAttrKey /\<[a-zA-Z_-]\+\ze=/ containedin=ALL
syn match sugarAttrOp /=/ contained containedin=ALL
syn match sugarAttrVal /=[^ \t:]\+/ contains=sugarAttrOp,sugarInterp

" Boolean attributes
syn keyword sugarBoolAttr module disabled checked selected required readonly
syn keyword sugarBoolAttr autofocus autoplay controls defer async hidden
syn keyword sugarBoolAttr multiple novalidate open reversed

" Implicit child (line starting with :)
syn match sugarImplicitChild /^\s*: / containedin=ALL

" Inline element in text (tag after : in text content)
syn match sugarInlineTag /:\s\+\zs\(a\|span\|strong\|em\|b\|i\|code\|small\|mark\|abbr\|sub\|sup\)\>/

" HTML entities
syn match sugarEntity /&\w\+;/
syn match sugarEntity /&#\d\+;/

" ============================================================
" TEMPLATE CONTEXT (for/if in HTML)
" ============================================================

" for loop in HTML
syn match sugarTemplateFor /^\s*\zsfor\s\+.\+\s\+\(of\|in\)\s\+.\+/ contains=sugarTemplateForKw,sugarTemplateOfIn
syn keyword sugarTemplateForKw for contained
syn keyword sugarTemplateOfIn of in contained

" if conditional in HTML
syn match sugarTemplateIf /^\s*\zsif\s\+.\+/ contains=sugarTemplateIfKw
syn keyword sugarTemplateIfKw if contained

" ============================================================
" COMPONENT CONTEXT
" ============================================================

" Component definition: name = (params):
syn match sugarComponentDef /^\s*\zs\w\+\s*=\s*([^)]*)/ contains=sugarComponentName,sugarComponentParams,sugarComponentEq
syn match sugarComponentName /\w\+\ze\s*=/ contained
syn match sugarComponentEq /=/ contained
syn match sugarComponentParams /([^)]*)/ contained contains=sugarParamName
syn match sugarParamName /\w\+/ contained

" Component call: name(args) — not an HTML tag
syn match sugarComponentCall /^\s*\zs\(card\|panel\|modal\|field\|selectfield\|navlink\|filterbtn\|\w\+\)\s*([^)]*)\ze\s*:/ contains=sugarCallName,sugarCallArgs
syn match sugarCallName /\w\+\ze\s*(/ contained
syn match sugarCallArgs /([^)]*)/ contained contains=sugarString,sugarNumber

" ============================================================
" STYLE CONTEXT (inside style:)
" ============================================================

" CSS selectors
syn match sugarCSSSelector /^\s*\zs[.#@:][a-zA-Z_:*-][a-zA-Z0-9_:/.+-]*/
syn match sugarCSSSelector /^\s*\zs\*\s*$/
syn match sugarCSSSelector /^\s*\zs[a-z][a-z0-9-]*\ze\s*:$/

" CSS properties
syn keyword sugarCSSProp contained margin padding border background color font display
syn keyword sugarCSSProp contained position width height top left right bottom overflow
syn keyword sugarCSSProp contained opacity transform transition animation flex grid gap
syn keyword sugarCSSProp contained align justify text box cursor outline resize content
syn keyword sugarCSSProp contained visibility z-index float clear appearance
syn match sugarCSSPropMatch /^\s*\zs[a-z-]\+\ze: / containedin=ALL

" CSS values — colors
syn match sugarCSSColor /#[0-9a-fA-F]\{3,8\}/
syn match sugarCSSFunc /\<\(rgb\|rgba\|hsl\|hsla\|var\|calc\|min\|max\|clamp\|url\|linear-gradient\|radial-gradient\)\>/

" CSS units
syn match sugarCSSUnit /\<\d\+\(\.\d\+\)\?\(px\|em\|rem\|vh\|vw\|%\|s\|ms\|deg\|fr\)\>/

" CSS at-rules
syn match sugarAtRule /^\s*\zs@\(keyframes\|media\|import\|font-face\|supports\|layer\)\>/

" CSS mixin definition: name = ():
syn match sugarMixinDef /^\s*\zs\w\+\s*=\s*()\ze\s*:/

" CSS mixin call: @name()
syn match sugarMixinCall /@\w\+()/

" ============================================================
" SCRIPT CONTEXT (inside script:)
" ============================================================

" JS keywords
syn keyword sugarJSKeyword if else for while do switch case break continue
syn keyword sugarJSKeyword return throw try catch finally
syn keyword sugarJSKeyword class extends new typeof instanceof in of
syn keyword sugarJSKeyword async await yield import export default from
syn keyword sugarJSKeyword const let var this super delete void

" JS built-in objects
syn keyword sugarJSBuiltin console document window Math JSON Object Array
syn keyword sugarJSBuiltin String Number Boolean Date RegExp Map Set Promise
syn keyword sugarJSBuiltin Error setTimeout setInterval requestAnimationFrame
syn keyword sugarJSBuiltin parseInt parseFloat isNaN fetch localStorage

" JS constants
syn keyword sugarJSBool true false
syn keyword sugarJSNull null undefined NaN Infinity

" JS operators
syn match sugarJSOp /[=!<>]=\?/
syn match sugarJSOp /[+\-*/%]/
syn match sugarJSOp /&&\|||\|!!/
syn match sugarJSOp /=>/
syn match sugarJSOp /\.\.\./
syn match sugarJSOp /??\|?\./

" JS function/method definition: name(args):
syn match sugarJSFunc /\<\w\+\s*\ze([^)]*)\s*:/

" JS property access
syn match sugarJSProp /\.\zs\w\+/

" ============================================================
" HIGHLIGHTING
" ============================================================

" Comments
hi def link sugarComment Comment

" Strings and templates
hi def link sugarString String
hi def link sugarTemplateLit String
hi def link sugarTemplateExpr Special
hi def link sugarInterp Special

" Numbers
hi def link sugarNumber Number

" HTML
hi def link sugarTag Keyword
hi def link sugarVoid Keyword
hi def link sugarSlot PreProc
hi def link sugarClass Type
hi def link sugarID Identifier
hi def link sugarAttrKey Label
hi def link sugarAttrOp Operator
hi def link sugarAttrVal String
hi def link sugarBoolAttr Label
hi def link sugarImplicitChild Delimiter
hi def link sugarInlineTag Keyword
hi def link sugarEntity SpecialChar
hi def link sugarColon Delimiter

" Template
hi def link sugarTemplateFor Statement
hi def link sugarTemplateForKw Repeat
hi def link sugarTemplateOfIn Repeat
hi def link sugarTemplateIf Conditional
hi def link sugarTemplateIfKw Conditional

" Components
hi def link sugarComponentDef Function
hi def link sugarComponentName Function
hi def link sugarComponentEq Operator
hi def link sugarComponentParams Special
hi def link sugarParamName Identifier
hi def link sugarComponentCall Function
hi def link sugarCallName Function
hi def link sugarCallArgs Special

" CSS
hi def link sugarCSSSelector Structure
hi def link sugarCSSPropMatch Type
hi def link sugarCSSColor Constant
hi def link sugarCSSFunc Function
hi def link sugarCSSUnit Number
hi def link sugarAtRule PreProc
hi def link sugarMixinDef Function
hi def link sugarMixinCall PreProc

" JS
hi def link sugarJSKeyword Statement
hi def link sugarJSBuiltin Identifier
hi def link sugarJSBool Boolean
hi def link sugarJSNull Constant
hi def link sugarJSOp Operator
hi def link sugarJSFunc Function
hi def link sugarJSProp Identifier

let b:current_syntax = "sugar"
