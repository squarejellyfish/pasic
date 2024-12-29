TARGET = main
SRC = ./src/lex.py ./src/emit.py ./src/parse.py
EX_FILE = main.bas

$(TARGET): pasic.py $(SRC) $(EX_FILE)
	python pasic.py $(EX_FILE)

asm: out.asm
	nasm -felf64 -g out.asm
	ld out.o -o out
	./out

rule110: rule110.c
	gcc rule110.c -o rule110
	./rule110

.PHONY: clean all
clean:
	rm $(TARGET) $(TARGET).asm $(TARGET).o parse.json parse.xml
all: clean $(TARGET)
