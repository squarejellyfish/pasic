TARGET = main
SRC = ./src/lex.py ./src/emit.py ./src/parse.py
EX_FILE = main.pasic std/std.pasic

$(TARGET): pasic.py $(SRC) $(EX_FILE)
	python3 pasic.py $(EX_FILE)

asm: main.asm
	nasm -felf64 -g $(TARGET).asm
	ld $(TARGET).o -o $(TARGET)
	./$(TARGET)

rule110: rule110.c
	gcc rule110.c -o rule110
	./rule110

test: tests test.py
	python3 test.py tests

.PHONY: clean all
clean:
	rm $(TARGET) $(TARGET).asm $(TARGET).o parse.json 
all: clean $(TARGET)
