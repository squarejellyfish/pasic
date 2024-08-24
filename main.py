from lex import *
from parse import *
from emit import *
from pathlib import Path
import subprocess
import sys

def main():

    if len(sys.argv) != 2:
        sys.exit("Error: no input file.")
    fileName = sys.argv[1]
    outputName = Path("out.c")
    with open(fileName, 'r') as inputFile:
        source = inputFile.read()

    lexer = Lexer(source, fileName)
    emitter = Emitter(outputName.name)
    parser = Parser(lexer, emitter)

    parser.program()
    emitter.writeFile()

    subprocess.run(["gcc", outputName.name, "-o", outputName.stem])
    subprocess.run([f"./{outputName.stem}"])

if __name__ == "__main__":
    main()
