" Vim syntax file for Sugar template language
if exists("b:current_syntax")
  finish
endif

syn case match

" Priority in vim: later definitions win. Order matters.

" ── 1. Base: colon separator (lowest priority) ─────────────

syn match sugarColon /:/

" ── 2. Comments (always win — defined early but with high prio) ─

syn match sugarComment /^\s*#\s.*$/ contains=NONE

" ── 3. Strings ─────────────────────────────────────────────

syn region sugarString start=/"/ skip=/\\"/ end=/"/
syn region sugarString start=/'/ skip=/\\'/ end=/'/
syn region sugarTemplateLit start=/`/ skip=/\\`/ end=/`/ contains=sugarTemplateExpr
syn match sugarTemplateExpr /\${[^}]*}/ contained

" ── 4. Numbers ─────────────────────────────────────────────

" Only match numbers after whitespace, =, (, ,, : or start of line (not inside class names like .gray-400)
syn match sugarNumber /\([\s=:(,]\|^\)\zs\d\+\(\.\d\+\)\?\>/
syn match sugarCSSUnit /\([\s=:(,]\|^\)\d\+\(\.\d\+\)\?\zs\(px\|em\|rem\|vh\|vw\|%\|s\|ms\|deg\|fr\)\>/

" ── 5. HTML entities ───────────────────────────────────────

syn match sugarEntity /&[#a-zA-Z0-9]\+;/

" ── 6. JS keywords ─────────────────────────────────────────

syn keyword sugarJSKw const let var this new typeof instanceof delete void super
syn keyword sugarJSKw import export default from switch case break continue do yield
syn keyword sugarBuiltin console document window Math JSON Object Array
syn keyword sugarBuiltin String Number Boolean Date Promise Error
syn keyword sugarBuiltin setTimeout setInterval requestAnimationFrame
syn keyword sugarBuiltin parseInt parseFloat isNaN fetch localStorage

" ── 7. Constants ───────────────────────────────────────────

syn keyword sugarConstant true false null undefined NaN Infinity

" ── 8. Operators ───────────────────────────────────────────

syn match sugarOp /=>/
syn match sugarOp /===\|!==\|==\|!=/
syn match sugarOp /&&\|||\|??/
syn match sugarOp /\.\.\./

" ── 9. Attributes: key=value ───────────────────────────────

syn match sugarAttr /\s[a-zA-Z_-]\+=\S*/ contains=sugarAttrKey,sugarAttrEq,sugarAttrVal,sugarInterp
syn match sugarAttrKey /[a-zA-Z_-]\+\ze=/ contained
syn match sugarAttrEq /=/ contained
syn match sugarAttrVal /=\zs[^ \t:]*/ contained contains=sugarInterp

" Boolean attributes (after a tag/class chain)
syn keyword sugarBoolAttr module disabled checked selected required readonly
syn keyword sugarBoolAttr autofocus autoplay controls defer hidden multiple

" ── 10. CSS specifics ──────────────────────────────────────

syn match sugarAtRule /^\s*\zs@\(keyframes\|media\|import\|font-face\|supports\|layer\)\>/
syn match sugarMixinCall /^\s*\zs@\w\+()/
syn match sugarCSSColor /#[0-9a-fA-F]\{3,8\}\>/
syn match sugarCSSFunc /\<\(rgb\|rgba\|hsl\|hsla\|var\|calc\|url\)\ze(/

" ── 11. Line-start keywords (for/if/else/while/class...) ──

syn match sugarKeyword /^\s*\zs\(for\|if\|else\|while\|try\|catch\|finally\|class\|async\|return\|await\|throw\)\>/
syn match sugarKeywordOf /\s\zs\(of\|in\|extends\)\ze\s/

" ── 12. Tags — match the tag NAME before . or # or space ──

" tag.class: or tag#id: or tag attr=:  or tag:
syn match sugarTag /^\s*\zs\(html\|head\|body\|div\|span\|p\|a\|ul\|ol\|li\|table\|thead\|tbody\|tfoot\|tr\|td\|th\|h[1-6]\|img\|input\|button\|form\|label\|select\|option\|textarea\|header\|footer\|main\|nav\|section\|article\|aside\|canvas\|pre\|code\|blockquote\|iframe\|video\|audio\|source\|figure\|figcaption\|details\|summary\|dialog\|dl\|dt\|dd\|em\|strong\|b\|i\|small\|mark\|del\|ins\|sub\|sup\|br\|hr\|meta\|link\|title\|style\|script\)\ze[.#: \t]/

" Inline tag after : in text
syn match sugarTag /:\s\+\zs\(a\|span\|strong\|em\|b\|i\|code\|small\|mark\)\ze\s/

" ── 13. Slot (distinct) ───────────────────────────────────

syn match sugarSlot /^\s*\zsslot\ze\s*:/

" ── 14. Classes — .name chains (AFTER tags so they win) ───

" Class starting a line (implicit div): .foo.bar:
syn match sugarClass /^\s*\zs\(\.[a-zA-Z_-][a-zA-Z0-9_.:/+-]*\)\+/

" Class after tag: h3.foo.bar (just the .foo.bar part)
syn match sugarClass /\(html\|head\|body\|div\|span\|p\|a\|ul\|ol\|li\|table\|thead\|tbody\|tfoot\|tr\|td\|th\|h[1-6]\|img\|input\|button\|form\|label\|select\|option\|textarea\|header\|footer\|main\|nav\|section\|article\|aside\|canvas\|pre\|code\|blockquote\|iframe\|video\|audio\|source\|figure\|figcaption\|details\|summary\|dialog\|dl\|dt\|dd\|em\|strong\|b\|i\|small\|mark\|del\|ins\|sub\|sup\|br\|hr\|meta\|link\|title\|style\|script\)\zs\(\.[a-zA-Z_-][a-zA-Z0-9_.:/+-]*\)\+/

" ── 15. IDs — #name (AFTER classes so yellow wins) ────────

syn match sugarID /#[a-zA-Z_-][a-zA-Z0-9_-]*/

" ── 16. Interpolation {expr} (high priority) ──────────────

syn match sugarInterp /{[^}]\+}/

" ── 17. Implicit child :  (high priority) ─────────────────

syn match sugarImplicit /^\s*\zs:\ze\s/

" ── 18. Component/function defs (highest priority) ────────

" Component def: name = (params):
syn match sugarFuncDef /^\s*\zs\w\+\ze\s*=\s*(/

" Method/function def: name(args): at end of line
syn match sugarFuncDef /^\s*\(async\s\+\)\?\zs\w\+\ze\s*([^)]*)\s*:\s*$/

" Component call: name(...) at start of line (not a known tag)
syn match sugarFuncCall /^\s*\zs\w\+\ze\s*(/

" ── 19. Comments again (absolute highest priority) ────────

syn match sugarComment /^\s*#\s.*$/ contains=NONE

" ── Colors ─────────────────────────────────────────────────

hi sugarComment      guifg=#6b7280 ctermfg=244  gui=italic cterm=italic
hi sugarString       guifg=#86efac ctermfg=120
hi sugarTemplateLit  guifg=#86efac ctermfg=120
hi sugarTemplateExpr guifg=#fbbf24 ctermfg=220
hi sugarNumber       guifg=#fdba74 ctermfg=216
hi sugarCSSUnit      guifg=#fdba74 ctermfg=216
hi sugarCSSColor     guifg=#fdba74 ctermfg=216
hi sugarCSSFunc      guifg=#67e8f9 ctermfg=87
hi sugarEntity       guifg=#fdba74 ctermfg=216
hi sugarConstant     guifg=#fdba74 ctermfg=216
hi sugarOp           guifg=#94a3b8 ctermfg=248
hi sugarColon        guifg=#4b5563 ctermfg=240
hi sugarJSKw         guifg=#f472b6 ctermfg=212
hi sugarBuiltin      guifg=#67e8f9 ctermfg=87
hi sugarBoolAttr     guifg=#a5b4fc ctermfg=147
hi sugarAttr         guifg=#a5b4fc ctermfg=147
hi sugarAttrKey      guifg=#a5b4fc ctermfg=147
hi sugarAttrEq       guifg=#6b7280 ctermfg=244
hi sugarAttrVal      guifg=#c7d2fe ctermfg=189
hi sugarAtRule       guifg=#c084fc ctermfg=177  gui=bold cterm=bold
hi sugarMixinCall    guifg=#a78bfa ctermfg=141
hi sugarKeyword      guifg=#f472b6 ctermfg=212
hi sugarKeywordOf    guifg=#f472b6 ctermfg=212
hi sugarTag          guifg=#c084fc ctermfg=177
hi sugarSlot         guifg=#f472b6 ctermfg=212  gui=bold cterm=bold
hi sugarClass        guifg=#22d3ee ctermfg=80
hi sugarID           guifg=#fbbf24 ctermfg=220  gui=bold cterm=bold
hi sugarInterp       guifg=#fbbf24 ctermfg=220  gui=bold cterm=bold
hi sugarImplicit     guifg=#6b7280 ctermfg=244  gui=bold cterm=bold
hi sugarFuncDef      guifg=#34d399 ctermfg=79   gui=bold cterm=bold
hi sugarFuncCall     guifg=#34d399 ctermfg=79

let b:current_syntax = "sugar"
