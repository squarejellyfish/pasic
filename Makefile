TARGET = out
SRC = main.bas

$(TARGET): parse.py lex.py emit.py pasic.py $(SRC)
	python pasic.py $(SRC)

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
