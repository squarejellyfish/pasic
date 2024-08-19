from lex import *
from parse import *
from emit import *
import sys

def main():

    if len(sys.argv) != 2:
        sys.exit("Error: no input file.")
    with open(sys.argv[1], 'r') as inputFile:
        source = inputFile.read()

    lexer = Lexer(source)
    emitter = Emitter("out.c")
    parser = Parser(lexer, emitter)

    parser.program()
    emitter.writeFile()

if __name__ == "__main__":
    main()
