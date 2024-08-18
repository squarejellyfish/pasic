from lex import *
from parse import *
import sys

def main():

    if len(sys.argv) != 2:
        sys.exit("Error: no input file.")
    with open(sys.argv[1], 'r') as inputFile:
        source = inputFile.read()

    lexer = Lexer(source)
    parser = Parser(lexer)

    parser.program()
    print("Parsing completed.")

if __name__ == "__main__":
    main()
