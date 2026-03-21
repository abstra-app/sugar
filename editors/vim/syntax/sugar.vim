" Vim syntax file for Sugar template language
if exists("b:current_syntax")
  finish
endif

syn case match

" ── Low priority (base layer) ───────────────────────────────

" Text after colon (content)
syn match sugarText /:\s\zs.\+$/ contains=sugarInterp,sugarString,sugarTemplateLit,sugarInlineTag,sugarEntity

" Colon separator
syn match sugarColon /:/

" ── Tags ────────────────────────────────────────────────────

" HTML tag at start of line (before . # space or :)
syn match sugarTag /^\s*\zs\(html\|head\|body\|div\|span\|p\|a\|ul\|ol\|li\|table\|thead\|tbody\|tr\|td\|th\|h[1-6]\|img\|input\|button\|form\|label\|select\|option\|textarea\|header\|footer\|main\|nav\|section\|article\|aside\|canvas\|pre\|code\|blockquote\|iframe\|video\|audio\|source\|figure\|figcaption\|details\|summary\|dialog\|dl\|dt\|dd\|em\|strong\|b\|i\|small\|mark\|del\|ins\|sub\|sup\|br\|hr\|meta\|link\|title\|style\|script\)\ze[.# :]/

" Inline tag in text content
syn match sugarInlineTag /:\s\+\zs\(a\|span\|strong\|em\|b\|i\|code\|small\)\ze\s/

" slot keyword
syn match sugarSlot /^\s*\zsslot\ze:/

" ── Classes and IDs (higher priority than tags) ─────────────

" Class chain: .foo.bar.baz (whole chain)
syn match sugarClass /\.[a-zA-Z_-][a-zA-Z0-9_.:/+-]*/

" ID: #name
syn match sugarID /#[a-zA-Z_-][a-zA-Z0-9_-]*/

" ── Attributes ──────────────────────────────────────────────

" key=value
syn match sugarAttr /\s\zs[a-zA-Z_-]\+=[^ \t:]*/  contains=sugarAttrEq
syn match sugarAttrEq /=/ contained

" Boolean attributes (standalone words after tag)
syn keyword sugarBoolAttr module disabled checked selected required readonly
syn keyword sugarBoolAttr autofocus autoplay controls defer hidden multiple

" ── Strings ─────────────────────────────────────────────────

syn region sugarString start=/"/ skip=/\\"/ end=/"/
syn region sugarString start=/'/ skip=/\\'/ end=/'/
syn region sugarTemplateLit start=/`/ skip=/\\`/ end=/`/ contains=sugarTemplateExpr
syn match sugarTemplateExpr /\${[^}]*}/ contained

" ── Interpolation ───────────────────────────────────────────

syn match sugarInterp /{[^}]\+}/

" ── Numbers ─────────────────────────────────────────────────

syn match sugarNumber /\<\d\+\(\.\d\+\)\?\>/

" ── HTML entities ───────────────────────────────────────────

syn match sugarEntity /&[#a-zA-Z0-9]\+;/

" ── Implicit child ──────────────────────────────────────────

syn match sugarImplicit /^\s*\zs:\ze\s/

" ── Keywords (for/if/else/while/class etc.) ─────────────────

syn match sugarKeyword /^\s*\zs\(for\|if\|else\|while\|try\|catch\|finally\|class\|async\|return\|await\|throw\)\>/
syn match sugarKeywordOf /\s\zs\(of\|in\|extends\)\ze\s/

" JS keywords inside lines
syn keyword sugarJSKw const let var this new typeof instanceof delete void super
syn keyword sugarJSKw import export default from switch case break continue do yield

" ── Builtins ────────────────────────────────────────────────

syn keyword sugarBuiltin console document window Math JSON Object Array
syn keyword sugarBuiltin String Number Boolean Date Promise Error
syn keyword sugarBuiltin setTimeout setInterval requestAnimationFrame
syn keyword sugarBuiltin parseInt parseFloat isNaN fetch localStorage

syn keyword sugarConstant true false null undefined NaN Infinity

" ── Operators ───────────────────────────────────────────────

syn match sugarOp /=>/
syn match sugarOp /[=!<>]=\=/
syn match sugarOp /&&\|||\|??/
syn match sugarOp /\.\.\./

" ── CSS specifics ───────────────────────────────────────────

syn match sugarAtRule /^\s*\zs@\(keyframes\|media\|import\|font-face\|supports\|layer\)\>/
syn match sugarMixinCall /^\s*\zs@\w\+()/
syn match sugarCSSColor /#[0-9a-fA-F]\{3,8\}\>/
syn match sugarCSSFunc /\<\(rgb\|rgba\|hsl\|hsla\|var\|calc\|url\|linear-gradient\)\ze(/
syn match sugarCSSUnit /\d\zs\(px\|em\|rem\|vh\|vw\|%\|s\|ms\|deg\|fr\)\>/

" ── Component/function definitions (highest priority) ──────

" Component def: name = (params):
syn match sugarFuncDef /^\s*\zs\w\+\ze\s*=\s*(/
syn match sugarFuncDefEq /\s\zs=\ze\s*(/

" Function/method def in script: name(args):
syn match sugarFuncDef /^\s*\(async\s\+\)\?\zs\w\+\ze\s*([^)]*)\s*:$/

" Component call: name(args)
syn match sugarFuncCall /^\s*\zs\w\+\ze\s*(/

" Params in parens (for defs)
syn match sugarParams /(\zs[^)]*\ze)/ contains=sugarParamName
syn match sugarParamName /\w\+/ contained

" ── Comments (highest priority — always wins) ───────────────

syn match sugarComment /^\s*# .*$/

" ── Highlighting with explicit colors ───────────────────────

" Use gui colors for truecolor terminals + cterm fallback

hi sugarComment     guifg=#6b7280 ctermfg=244  gui=italic cterm=italic
hi sugarTag         guifg=#c084fc ctermfg=177
hi sugarInlineTag   guifg=#c084fc ctermfg=177
hi sugarSlot        guifg=#f472b6 ctermfg=212  gui=bold cterm=bold
hi sugarClass       guifg=#22d3ee ctermfg=80
hi sugarID          guifg=#fbbf24 ctermfg=220
hi sugarAttr        guifg=#a5b4fc ctermfg=147
hi sugarAttrEq      guifg=#6b7280 ctermfg=244
hi sugarBoolAttr    guifg=#a5b4fc ctermfg=147
hi sugarString      guifg=#86efac ctermfg=120
hi sugarTemplateLit guifg=#86efac ctermfg=120
hi sugarTemplateExpr guifg=#fbbf24 ctermfg=220
hi sugarInterp      guifg=#fbbf24 ctermfg=220  gui=bold cterm=bold
hi sugarNumber      guifg=#fdba74 ctermfg=216
hi sugarEntity      guifg=#fdba74 ctermfg=216
hi sugarImplicit    guifg=#6b7280 ctermfg=244  gui=bold cterm=bold
hi sugarKeyword     guifg=#f472b6 ctermfg=212
hi sugarKeywordOf   guifg=#f472b6 ctermfg=212
hi sugarJSKw        guifg=#f472b6 ctermfg=212
hi sugarBuiltin     guifg=#67e8f9 ctermfg=87
hi sugarConstant    guifg=#fdba74 ctermfg=216
hi sugarOp          guifg=#94a3b8 ctermfg=248
hi sugarColon       guifg=#4b5563 ctermfg=240
hi sugarText        guifg=#e5e7eb ctermfg=254
hi sugarAtRule      guifg=#c084fc ctermfg=177  gui=bold cterm=bold
hi sugarMixinCall   guifg=#a78bfa ctermfg=141
hi sugarCSSColor    guifg=#fdba74 ctermfg=216
hi sugarCSSFunc     guifg=#67e8f9 ctermfg=87
hi sugarCSSUnit     guifg=#fdba74 ctermfg=216
hi sugarFuncDef     guifg=#34d399 ctermfg=79   gui=bold cterm=bold
hi sugarFuncDefEq   guifg=#6b7280 ctermfg=244
hi sugarFuncCall    guifg=#34d399 ctermfg=79
hi sugarParams      guifg=#e5e7eb ctermfg=254
hi sugarParamName   guifg=#e5e7eb ctermfg=254

let b:current_syntax = "sugar"
