" Vim syntax file
" Language:    Pasic
"
if exists("b:current_syntax")
  finish
endif
"
"
syn keyword     pasicKeywords   if then else while do end goto return let func include

syn keyword	pasicFunctions		print syscall

syn keyword     pasicType    __mem__

" Preprocessor
syn region	pasicPreProcDefine	start="^#define" skip="\\$" end="$" end="//"me=s-1 contains=pasicNumber,pasicComment
" syn region	pasicPreProcCondit	start="^\s*\(%:\|#\)\s*\(if\|ifdef\|ifndef\|elif\)\>" skip="\\$" end="$" end="//"me=s-1 contains=pasicComment
" syn match	pasicPreProcCondit	display "^\s*\(%:\|#\)\s*\(else\|endif\)\>"

"	Do the Basic variables names first.  This is because it
"	is the most inclusive of the tests.  Later on we change
"	this so the identifiers are split up into the various
"	types of identifiers like functions, basic commands and
"	such. MEM 9/9/2006
"
syn match	pasicIdentifier		"\<[a-z_][a-zA-Z0-9_]*\>"
syn match	pasicGenericFunction	"\<[a-z_][a-zA-Z0-9_]*\>\s*("me=e-1,he=e-1
syn match	pasicConstant	        "\<[A-Z][A-Z0-9_]*\>"
"
"	Function list
"
"	Catch errors caused by wrong parenthesis
"
syn region	pasicParen		transparent start='(' end=')' contains=ALLBUT,@pasicParenGroup
syn match	pasicParenError	")"
syn match	pasicInParen	contained "[{}]"
syn cluster	pasicParenGroup	contains=pasicParenError,pasicSpecial,pasicTodo,pasicUserCont,pasicUserLabel,pasicBitField
"
"	Integer number, or floating point number without a dot and with "f".
"	Hex end marking isn't quite right. Requires a space. Not sure how to
"	make that better
"
syn region	pasicHex		start="&h" end="\W"
syn match	pasicInteger	"\<\d\+\(u\=l\=\|lu\|f\)\>"
"
" "	Floating point number, with dot, optional exponent
" "
" syn match	pasicFloat		"\<\d\+\.\d*\(e[-+]\=\d\+\)\=[fl]\=\>"
" "
" "	Floating point number, starting with a dot, optional exponent
" "
" syn match	pasicFloat		"\.\d\+\(e[-+]\=\d\+\)\=[fl]\=\>"
" "
" "	Floating point number, without dot, with exponent
" "
" syn match	pasicFloat		"\<\d\+e[-+]\=\d\+[fl]\=\>"
"
"	Hex number
"
" syn case match
" syn match	pasicOctal		"\<0\o*\>"
" syn match	pasicOctalError	"\<0\o*[89]"
"
"	String and Character contstants
"
syn region	pasicString		start='"' end='"' contains=pasicSpecial,pasicTodo
"
"	Now do the comments and labels
"
syn match	pasicLabel		"\<^\w+:\>"
"
"	Create the clusters
"
syn cluster	pasicNumber		contains=pasicHex,pasicOctal,pasicInteger
"
"	Used with OPEN statement
"
syn match	pasicFilenumber	"#\d\+"
syn match	pasicMathOperator	"[\+\-\=\|\*\/\>\<\%\()[\]]" contains=pasicParen


"
"	Comments
"
syn region	pasicComment	start="//" end="$" contains=pasicSpecial,pasicTodo


"
"	The default methods for highlighting.  Can be overridden later
"

" Define the default highlighting.
" For version 5.7 and earlier: only when not done already
" For version 5.8 and later: only when an item doesn't have highlighting yet
highlight default link pasicKeywords		Keyword
highlight default link pasicFunctions		Function
highlight default link pasicGenericFunction	Function

highlight default link pasicString		String
highlight default link pasicComment		Comment
highlight default link pasicIdentifier		Identifier

highlight default link pasicPreProcDefine	PreProc
highlight default link pasicConstant            PreProc
"
highlight default link pasicLabel		Label
highlight default link pasicMathOperator	Operator
highlight default link pasicInteger		Number
highlight default link pasicHex		Number
highlight default link pasicType		Type
highlight default link pasicTodo		Todo


let b:current_syntax = "pasic"

" vim: ts=8
