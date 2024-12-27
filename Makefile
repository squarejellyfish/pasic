TARGET = out

$(TARGET): parse.py lex.py emit.py pasic.py hello.bas
	python pasic.py hello.bas

asm: out.asm
	nasm -felf64 -g out.asm
	ld out.o -o out
	./out

.PHONY: clean all
clean:
	rm $(TARGET) $(TARGET).asm $(TARGET).o parse.json parse.xml
all: clean $(TARGET)
