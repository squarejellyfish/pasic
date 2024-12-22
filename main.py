from lex import *
from parse import *
from emit import *
from pathlib import Path
import sys
import json
import subprocess
from dicttoxml import dicttoxml

def main():
    if len(sys.argv) != 2:
        sys.exit("Error: no input file.")
    fileName = sys.argv[1]
    outputName = Path("out.asm")
    with open(fileName, 'r') as inputFile:
        source = inputFile.read()

    lexer = Lexer(source, fileName)
    emitter = Emitter(outputName.name)
    parser = Parser(lexer)

    program = parser.program()
    xml = dicttoxml(program, root=False, return_bytes=False, attr_type=True)
    with open('parse.xml', 'w') as file:
        file.write(xml)
    with open('parse.json', 'w') as file:
        json.dump(program, file, indent=2)
    emitter.fromdict(program)
    emitter.writeFile()

    subprocess.run(["nasm", "-felf64", outputName.name])
    subprocess.run(["ld", "-o", outputName.stem, f'{outputName.stem}.o'])
    subprocess.run([f"./{outputName.stem}"])

if __name__ == "__main__":
    main()
