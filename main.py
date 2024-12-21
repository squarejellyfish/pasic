from lex import *
from parse import *
from emit import *
from pathlib import Path
import subprocess
import sys
import json
from dicttoxml import dicttoxml

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

    program = parser.program()
    xml = dicttoxml(program, root=False, return_bytes=False, attr_type=False)
    with open('parse.xml', 'w') as file:
        file.write(xml)
    # emitter.writeFile()

    # subprocess.run(["gcc", outputName.name, "-o", outputName.stem])
    # subprocess.run([f"./{outputName.stem}"])

if __name__ == "__main__":
    main()
