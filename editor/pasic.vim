" Vim syntax file
" Language:    Pasic
" Maintainer:  Mark Manning <markem@airmail.net>
" Updated:     10/22/2006
"
" Description:
"
"	Based originally on the work done by Allan Kelly <Allan.Kelly@ed.ac.uk>
"	Updated by Mark Manning <markem@airmail.net>
"	Applied pasic support to the already excellent support
"	for standard basic syntax (like QB).
"
"	First version based on Micro$soft QBASIC circa
"	1989, as documented in 'Learn BASIC Now' by
"	Halvorson&Rygmyr. Microsoft Press 1989.  This syntax file
"	not a complete implementation yet.  Send suggestions to
"	the maintainer.
"
"	Quit when a (custom) syntax file was already loaded (Taken from c.vim)
"
"	Updated Feb 2015 by Michael Torrie <torriem@gmail.com>
"
"	fixed highlighting for numbers, changed dim, redim, and as to
"	pasicArrays so they look better
"
"	Fixed comments, added multi-line comments
"
"	Fixed preprocessor highlighting (wasn't working at all), mostly
"	working now, though occasionally colors the next line after a #define.
"	Added support for include once
"
"	Fixed error highlighting a bit (for some reason clustering isn't
"	working.  
"
"	Instead of defaulting to "Identifier" which marks every variable and
"	symbol, leave those the default text color.  Makes it more consistent
"	with C, Python, and other syntax highlighting in VIM.
"
"	Other things probably still missing and not working.  the ON something 
"	GOTO something syntax is not highlighted.  Nor is OPEN Cons. Select
"	Case is not highlighted either.
"
"	Update:	Michael Torrie (torriem@gmail.com)	2/20/2015 11:22pm
"		I've made a number of changes to the file to fix a lot of things
"		that just weren't working such as preprocessor directives (#ifdef,
"		#define, etc).  Fixed up comment handling a bit, and added multi-line
"		comments (/' '/).  Changed a few other classifications too to make
"		the code highlight more like how code is highlighted in other languages
"		such as C, Python, etc.  User-defined identifiers are not colored at
"		all, which makes code a lot more readable.  Numbers also were not being
"		highlighted at all before; not sure why but I fixed that.  There
"		are still some broken things I encounter once in a while, but overall
"		the highlighting is much improved.
"
if exists("b:current_syntax")
  finish
endif
"
"	Be sure to turn on the "case ignore" since current versions
"	of pasic support both upper as well as lowercase
"	letters. - MEM 10/1/2006
"
syn case ignore
"
"	This list of keywords is taken directly from the pasic
"	user's guide as presented by the pasic online site.
"
syn keyword     pasicKeywords   if then else while do end goto return let

syn keyword	pasicFunctions		print syscall write

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
syn match	pasicIdentifier		"\<[a-zA-Z_][a-zA-Z0-9_]*\>"
syn match	pasicGenericFunction	"\<[a-zA-Z_][a-zA-Z0-9_]*\>\s*("me=e-1,he=e-1
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

highlight default link pasicPreProcDefine	PreProc

highlight default link pasicString		String
highlight default link pasicComment		Comment

highlight default link pasicLabel		Label
highlight default link pasicMathOperator	Operator
highlight default link pasicInteger		Number
highlight default link pasicHex		Number
highlight default link pasicSpecial		Special
highlight default link pasicTodo		Todo

let b:current_syntax = "pasic"

" vim: ts=8
