default: parse.py lex.py emit.py main.py hello.bas
	python main.py hello.bas

asm: out.asm
	nasm -felf64 out.asm
	ld out.o -o out
	./out
